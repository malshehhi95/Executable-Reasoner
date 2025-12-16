# executable_reasoner.py
# pip install -U langchain langchain-community langchain-groq
# Optional (recommended for local dev): pip install -U python-dotenv

import os
import re
import sys
import json
import shlex
import pathlib
import subprocess
from dataclasses import dataclass
from typing import Optional, Set, Tuple

try:
    # Optional: loads GROQ_API_KEY from a local .env file (do NOT commit .env)
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate


# ----------------------------
# 0) Config
# ----------------------------
@dataclass(frozen=True)
class Settings:
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.0
    timeout_seconds: int = 60
    max_output_chars: int = 12000


BASE_DIR = pathlib.Path(__file__).resolve().parent
WORKSPACE = (BASE_DIR / "agent_workspace").resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

ALLOWED_WRITE_EXTS: Set[str] = {".py", ".txt", ".md", ".json", ".csv", ".log"}
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_\-\.]")


def _sanitize_filename(name: str) -> str:
    name = (name or "").strip()
    name = name.replace("\\", "/").split("/")[-1]  # force flat workspace files
    name = SAFE_NAME_RE.sub("_", name).strip("._") or "task"
    return name


def _safe_path(filename: str, default_ext: str, allowed_exts: Set[str]) -> pathlib.Path:
    clean = _sanitize_filename(filename)
    p = (WORKSPACE / clean).resolve()

    # Ensure inside workspace
    if not str(p).startswith(str(WORKSPACE)):
        raise ValueError("Invalid path (outside workspace).")

    # Ensure extension
    ext = p.suffix.lower()
    if not ext:
        p = p.with_suffix(default_ext)
        ext = default_ext.lower()

    if ext not in allowed_exts:
        raise ValueError(f"Extension not allowed: {ext}. Allowed: {sorted(allowed_exts)}")

    return p


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    head = s[: limit // 2]
    tail = s[-(limit // 2) :]
    return head + "\n\n...[TRUNCATED]...\n\n" + tail


# ----------------------------
# 1) Tools the agent can use
# ----------------------------
@tool
def write_file(spec: str) -> str:
    """
    Create/overwrite a text file in the workspace.
    Input 'spec' must be JSON with fields:
      - "filename": str (example: "script.py", "notes.md", "data.json")
      - "content": str
    Returns the saved path.
    """
    try:
        obj = json.loads(spec)
        filename = obj.get("filename", "task.txt")
        content = obj.get("content", "")
        path = _safe_path(filename, default_ext=".txt", allowed_exts=ALLOWED_WRITE_EXTS)
        path.write_text(content, encoding="utf-8")
        return f"Saved: {path}"
    except Exception as e:
        return f"Error in write_file: {e}"


@tool
def write_python_file(spec: str) -> str:
    """
    Backward compatible tool: writes a .py file.
    Input JSON:
      - "filename": str
      - "code": str
    """
    try:
        obj = json.loads(spec)
        filename = obj.get("filename", "task.py")
        code = obj.get("code", "")
        path = _safe_path(filename, default_ext=".py", allowed_exts={".py"})
        path.write_text(code, encoding="utf-8")
        return f"Saved: {path}"
    except Exception as e:
        return f"Error in write_python_file: {e}"


@tool
def run_python(tool_input: str) -> str:
    """
    Run a Python file in the workspace (optionally with args).
    Pass a single string like: 'my_script.py --flag 3'
    """
    try:
        cmdline = (tool_input or "").strip()
        if not cmdline:
            return "Error: No command provided."

        parts = shlex.split(cmdline)
        file = parts[0]

        path = _safe_path(file, default_ext=".py", allowed_exts={".py"})
        if not path.exists():
            return f"Error: File not found: {path.name}"

        cmd = [sys.executable, str(path)] + parts[1:]
        proc = subprocess.run(
            cmd,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=SETTINGS.timeout_seconds,
        )

        out = proc.stdout or ""
        err = proc.stderr or ""
        out = _truncate(out, SETTINGS.max_output_chars)
        err = _truncate(err, SETTINGS.max_output_chars)

        return (
            f"[STDOUT]\n{out}\n"
            f"[STDERR]\n{err}\n"
            f"[RETURN_CODE]\n{proc.returncode}"
        )
    except subprocess.TimeoutExpired:
        return "Error: Execution timed out."
    except Exception as e:
        return f"Error in run_python: {e}"


@tool
def read_file(name: str) -> str:
    """
    Read a text file from the workspace (example: results.txt, output.json).
    Returns its content.
    """
    try:
        path = _safe_path(name, default_ext=".txt", allowed_exts=ALLOWED_WRITE_EXTS)
        if not path.exists():
            return f"Error: Not found: {path.name}"
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"Error in read_file: {e}"


@tool
def list_workspace(_: str = "") -> str:
    """List files in the workspace with sizes."""
    try:
        items = []
        for p in sorted(WORKSPACE.iterdir()):
            if p.is_file():
                items.append({"name": p.name, "size": p.stat().st_size})
            else:
                items.append({"name": p.name + "/", "size": 0})
        return json.dumps(items, indent=2)
    except Exception as e:
        return f"Error in list_workspace: {e}"


TOOLS = [write_file, write_python_file, run_python, read_file, list_workspace]


# ----------------------------
# 2) Model setup
# ----------------------------
SETTINGS = Settings()

def _require_api_key() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        msg = (
            "Missing GROQ_API_KEY.\n\n"
            "Set it in your shell:\n"
            "  macOS/Linux: export GROQ_API_KEY='your_key'\n"
            "  Windows PS:  $env:GROQ_API_KEY='your_key'\n\n"
            "Or create a local .env file (gitignored) with:\n"
            "  GROQ_API_KEY=your_key\n"
        )
        raise RuntimeError(msg)

_require_api_key()

llm = ChatGroq(model_name=SETTINGS.model_name, temperature=SETTINGS.temperature)


# ----------------------------
# 3) Agent prompt (ReAct)
# ----------------------------
PROMPT = ChatPromptTemplate.from_template("""\
You are a careful software agent that solves tasks by writing and running Python programs in a local workspace.

You have access to the following tools:
{tools}

You may call these tools by name: {tool_names}

Rules:
- Operate only inside the workspace. Do not request secrets or API keys.
- Prefer the Python standard library. Avoid network calls unless the user explicitly asks.
- When writing code, write complete runnable scripts.
- After execution, inspect outputs and fix errors iteratively.
- Keep your final response concise and actionable.

Use this format:
Thought: what to do next
Action: tool name (one of {tool_names})
Action Input: exact input
Observation: tool output
... repeat as needed ...
Final Answer: final result for the user

User question:
{input}

{agent_scratchpad}
""")

agent = create_react_agent(llm, TOOLS, PROMPT)
executor = AgentExecutor(agent=agent, tools=TOOLS, verbose=True, handle_parsing_errors=True)


# ----------------------------
# 4) CLI entry
# ----------------------------
def _get_task_from_args() -> Optional[str]:
    if len(sys.argv) >= 2:
        return " ".join(sys.argv[1:]).strip()
    return None


if __name__ == "__main__":
    print(f"Workspace: {WORKSPACE}")

    task = _get_task_from_args()
    if task:
        result = executor.invoke({"input": task})
        print("\n=== FINAL OUTPUT ===")
        print(result.get("output", "No output"))
        raise SystemExit(0)

    # REPL mode
    while True:
        user_task = input("\nWhat should I do? (type 'exit' to quit) ").strip()
        if not user_task:
            continue
        if user_task.lower() in {"exit", "quit"}:
            break

        result = executor.invoke({"input": user_task})
        print("\n=== FINAL OUTPUT ===")
        print(result.get("output", "No output"))
