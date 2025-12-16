# Executable-Reasoner
A local, tool-using coding agent that turns a natural language task into runnable Python scripts, executes them in a sandboxed workspace folder, inspects results, and iterates until the task is done.


This project uses:
- Groq LLM via `langchain-groq`
- LangChain ReAct agent pattern
- A small set of local tools (write file, run python, read file, list workspace)

## Why this exists

Many "AI coding assistants" stop at suggestions. This one is designed to actually:
1) write a complete script
2) run it locally
3) read outputs and error traces
4) fix issues and rerun

It is useful for:
- building small utilities quickly (parsers, converters, report generators)
- debugging and iterating on code in a repeatable workspace
- creating reproducible mini-experiments with logs and outputs saved to disk
- prototyping CLI tools, data cleaning steps, and automation scripts

## How it works (technical overview)

The agent is a ReAct loop:
- The LLM plans a step
- It calls a tool (example: `write_python_file`)
- It observes tool output (example: traceback, stdout)
- It refines the next step based on evidence

All writes and reads are constrained to `agent_workspace/` using safe path checks:
- flat filenames only (no directory traversal)
- allowed extensions for writing are limited
- python execution is limited to scripts inside the workspace

## Project structure

- `agent_code_builder.py` main entry
- `agent_workspace/` runtime folder created automatically (should be gitignored)

Recommended additions:
- `.gitignore` ignore `agent_workspace/` and `.env`
- `requirements.txt` for pinned dependencies

## Setup

### 1) Install dependencies

```bash
pip install -U langchain langchain-community langchain-groq
# optional for local development
pip install -U python-dotenv
