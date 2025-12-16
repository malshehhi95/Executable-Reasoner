# Executable Reasoner

**Executable Reasoner** is a local, tool-using AI agent that transforms natural language instructions into *verifiable execution*.  
It does not stop at suggestions. It writes code, runs it, inspects results, and iterates until the task is complete.

This project is built using **Groq LLMs**, **LangChain**, and the **ReAct (Reason + Act)** agent pattern.

---

## Why Executable Reasoner exists

Most AI coding tools generate text and hope you trust it.

Executable Reasoner follows a stricter philosophy:

> *Reasoning without execution is speculation. Execution without reasoning is chaos.*

This agent closes the loop by:
1. Reasoning about a task
2. Writing complete runnable programs
3. Executing them locally
4. Inspecting real outputs and errors
5. Refining until the result is correct

It behaves less like a chatbot and more like a junior engineer that must **prove its work**.

---

## Core capabilities

Executable Reasoner can:

- Generate full Python scripts from natural language
- Execute scripts inside a sandboxed workspace
- Inspect stdout, stderr, and return codes
- Read and write structured artifacts (JSON, CSV, Markdown, logs)
- Iterate autonomously using evidence from execution
- Maintain a persistent workspace for multi-step tasks

Typical use cases:
- Rapid prototyping of utilities and scripts
- Data cleaning and validation pipelines
- Log analysis and report generation
- CLI tool generation and debugging
- Reproducible experiments and mini-research tasks

---

## How it works (technical overview)

Executable Reasoner is a **ReAct-style agent**:

- The LLM produces a reasoning step
- A tool is selected (write file, run code, read output)
- The tool is executed locally
- The result is fed back to the model
- The loop continues until completion

All operations are constrained to a local `agent_workspace/` directory with strict safety checks.

### Execution loop

```
Think → Write → Run → Observe → Refine
```

This closed loop is what differentiates Executable Reasoner from traditional AI assistants.

---

## Project structure

```
.
├── agent_code_builder.py     # Main agent implementation
├── agent_workspace/          # Runtime workspace (auto-created, gitignored)
├── README.md
└── requirements.txt
```

The workspace persists between steps, allowing the agent to build upon previous outputs.

---

## Installation

### 1. Install dependencies

```bash
pip install -U langchain langchain-community langchain-groq
pip install -U python-dotenv   # optional but recommended
```

### 2. Set your Groq API key

**Never hardcode API keys.**

macOS / Linux:
```bash
export GROQ_API_KEY="your_key_here"
```

Windows PowerShell:
```powershell
$env:GROQ_API_KEY="your_key_here"
```

Optional `.env` file (do not commit):
```text
GROQ_API_KEY=your_key_here
```

---

## Usage

### One-shot mode

```bash
python agent_code_builder.py "Create a script that parses a CSV file and generates a summary report"
```

### Interactive REPL mode

```bash
python agent_code_builder.py
```

You can then issue multi-step instructions interactively.  
The agent will write files, run them, and refine results automatically.

---
## 3 complicated multi-step sample prompts (copy/paste)

### Prompt 1: Build a full mini pipeline with validation + report
“Create a complete mini data pipeline in the workspace:
1) Generate a synthetic CSV dataset for student performance with columns (student_id, program, attendance_rate, midterm, final, passed).
2) Write `clean_validate.py` that loads the CSV, validates types/ranges, fixes common issues, and outputs `clean.csv` plus `validation_report.json`.
3) Write `analysis_report.py` that reads `clean.csv` and produces `report.md` with key stats, pass rates by program, and correlation notes.
4) Run both scripts, show outputs, and list the workspace files at the end.”

### Prompt 2: Write a CLI tool + unit tests + bug fixing loop
“Build a CLI tool called `log_sleuth.py` that:
1) Generates a sample `app.log` with mixed INFO/WARN/ERROR lines and fake request ids.
2) Parses the log and outputs `summary.json` with counts per level, top 5 recurring error messages, and a timeline bucketed per minute.
3) Add a `--filter LEVEL` option and `--since-minutes N` option.
4) Create `test_log_sleuth.py` with at least 6 tests using `unittest`.
5) Run tests, fix failures until all pass, then show the final summary output.”

### Prompt 3: Build a local codebase indexer (like a tiny IDE brain)
“Inside the workspace:
1) Create 5 small Python modules (utilities, math, strings, io, main) with several functions and classes.
2) Write `indexer.py` that walks the workspace, parses all `.py` files using `ast`, extracts functions/classes/docstrings, and writes `code_index.json`.
3) Write `search_index.py` that loads `code_index.json` and supports keyword search plus ‘find functions that have more than N args’.
4) Run indexer, then run 3 different searches and show results.”
## Available tools

Executable Reasoner currently includes:

- `write_python_file` – write runnable Python scripts
- `write_file` – write text, JSON, CSV, Markdown files
- `run_python` – execute Python scripts safely
- `read_file` – inspect generated artifacts
- `list_workspace` – view workspace contents

These tools can be extended to support testing, formatting, or analysis workflows.

---

## Security considerations

This agent executes code locally.

Recommended precautions:
- Keep execution inside the provided workspace
- Do not add unrestricted shell or delete tools without approval gates
- Never expose secrets to the agent
- Consider running inside a container for stronger isolation

Executable Reasoner is intentionally conservative by default.

---

## Design philosophy

Executable Reasoner follows three principles:

1. **Evidence over confidence**
2. **Execution over suggestion**
3. **Iteration over assumption**

If a result cannot be executed and inspected, it is not considered complete.

---

## License

Choose an appropriate open-source license (MIT is common)  
and add a `LICENSE` file before publishing.

---

## Final note

Executable Reasoner is not designed to be impressive.

It is designed to be *correct*.
