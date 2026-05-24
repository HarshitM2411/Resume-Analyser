# Phase-wise Implementation Plan

## LLM-Powered File System Assistant

> Follows the specs in `context.md` and the architecture in `architecture.md`.  

> Each phase is self-contained, testable, and must pass before moving to the next.

---

## Quick Reference

| Phase | Goal | Primary File | Weight |

|-------|------|-------------|--------|

| 0 | Project scaffold | folders, `.env`, `requirements.txt` | — |

| 1 | `read_file()` | `fs_tools.py` | Part A (60%) |

| 2 | `list_files()` | `fs_tools.py` | Part A (60%) |

| 3 | `write_file()` | `fs_tools.py` | Part A (60%) |

| 4 | `search_in_file()` | `fs_tools.py` | Part A (60%) |

| 5 | Tool schemas | `llm_file_assistant.py` | Part B (40%) |

| 6 | Agentic loop | `llm_file_assistant.py` | Part B (40%) |

| 7 | End-to-end tests | all three example queries | validation |

---

## Phase 0 — Project Scaffold

### Goal

Create the folder structure, install dependencies, configure environment variables, and add sample resume files so all later phases have a working base to run against.

### Steps

**0.1 Create directories**

```bash

mkdir -p resumes output docs

```

**0.2 Create `requirements.txt`**

```

openai>=1.0.0

pdfplumber

python-docx

python-dotenv

```

**0.3 Install dependencies**

```bash

pip install -r requirements.txt

```

**0.4 Create `.env`** *(never commit this file)*

```

GROQ_API_KEY=gsk_...

LLM_PROVIDER=groq

LLM_MODEL=llama-3.3-70b-versatile

RESUMES_DIR=./resumes

OUTPUT_DIR=./output

```

> **Note:** Groq exposes an OpenAI-compatible Chat Completions API. The project uses the `openai` Python package as the client SDK with `base_url=https://api.groq.com/openai/v1`.

**0.5 Add `.gitignore`**

```

.env

**pycache**/

*.pyc

output/

```

**0.6 Add sample resume files**

Place at minimum one file of each format into `resumes/` so all three parsers can be exercised:

| File | Format |

|------|--------|

| `resumes/resume_john_doe.pdf` | PDF |

| `resumes/resume_jane_smith.docx` | DOCX |

| `resumes/resume_alice_wang.txt` | TXT |

**0.7 Create empty source files**

```bash

touch fs_[tools.py](http://tools.py) llm_file_[assistant.py](http://assistant.py)

```

### Exit Criteria

- `pip install -r requirements.txt` completes with no errors

- `resumes/` contains at least one file of each format

- `python -c "import pdfplumber, docx, openai, dotenv; print('OK')"` prints `OK`

---

## Phase 1 — `read_file()` Tool

### Goal

Implement the first tool in `fs_tools.py`. It must accept a filepath, detect the file format, extract plain text, normalize it, and return a structured dict. It must never raise an exception to the caller.

### Files Touched

- `fs_tools.py`

### Skeleton to fill in

```python

# fs_[tools.py](http://tools.py)

import os

import re

from pathlib import Path

from datetime import datetime

# ── security helpers ────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent

RESUMES_DIR = (PROJECT_ROOT / "resumes").resolve()

OUTPUT_DIR = (PROJECT_ROOT / "output").resolve()

def *is*relative_to(path: Path, root: Path) -> bool:

    """Python 3.8+ compatible check for whether path is inside root."""

    try:

        path.relative_to(root)

        return True

    except ValueError:

        return False

def *is*safe_read_path(filepath: str) -> bool:

    """Allow reads only from the resumes and output directories."""

    resolved = Path(filepath).expanduser().resolve(strict=False)

    return *is*relative_to(resolved, RESUMES_DIR) or *is*relative_to(resolved, OUTPUT_DIR)

def *is*safe_write_path(filepath: str) -> bool:

    """Allow writes only inside the output directory."""

    resolved = Path(filepath).expanduser().resolve(strict=False)

    return *is*relative_to(resolved, OUTPUT_DIR)

def *normalize*text(text: str) -> str:

    """Collapse runs of whitespace; strip leading/trailing blanks."""

    text = re.sub(r'\n{3,}', '\n\n', text)

    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()

```

### Implementation Steps

**1.1 — TXT branch**

```python

def *read*txt(filepath: str) -> str:

    with open(filepath, "r", encoding="utf-8") as f:

        return [f.read](http://f.read)()

```

**1.2 — PDF branch**

```python

def *read*pdf(filepath: str) -> str:

    import pdfplumber

    pages_text = []

    with [pdfplumber.open](http://pdfplumber.open)(filepath) as pdf:

        for page in pdf.pages:

            t = page.extract_text()

            if t:

                pages_text.append(t)

    if not pages_text:

        raise ValueError("Scanned PDF — no extractable text layer found")

    return "\n".join(pages_text)

```

**1.3 — DOCX branch**

```python

def *read*docx(filepath: str) -> str:

    from docx import Document

    doc = Document(filepath)

    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

```

**1.4 — Public `read_file()` dispatcher**

```python

def read_file(filepath: str) -> dict:

    try:

        if not *is*safe_read_path(filepath):

            return {"success": False, "filepath": filepath,

                    "error": "Path not allowed — outside permitted directories"}

        path = Path(filepath)

        if not path.exists():

            return {"success": False, "filepath": filepath,

                    "error": f"FileNotFoundError: {filepath} does not exist"}

        ext = path.suffix.lower()

        dispatch = {".txt": *read*txt, ".pdf": *read*pdf, ".docx": *read*docx}

        if ext not in dispatch:

            return {"success": False, "filepath": filepath,

                    "error": f"UnsupportedFormat: '{ext}' is not supported"}

        raw_text = dispatch[ext](filepath)

        content = *normalize*text(raw_text)

        stat = path.stat()

        metadata = {

            "filename": [path.name](http://path.name),

            "size_bytes": [stat.st](http://stat.st)_size,

            "word_count": len(content.split()),

            "modified_at": datetime.fromtimestamp([stat.st](http://stat.st)_mtime).isoformat(timespec="seconds"),

        }

        if ext == ".pdf":

            import pdfplumber

            with [pdfplumber.open](http://pdfplumber.open)(filepath) as pdf:

                metadata["page_count"] = len(pdf.pages)

        return {

            "success": True,

            "filepath": filepath,

            "format": ext.lstrip("."),

            "content": content,

            "metadata": metadata,

        }

    except Exception as e:

        return {"success": False, "filepath": filepath, "error": str(e)}

```

### Manual Smoke Tests

```python

from fs_tools import read_file

# TXT

r = read_file("resumes/resume_alice_wang.txt")

assert r["success"] is True

assert len(r["content"]) > 0

assert r["format"] == "txt"

# PDF

r = read_file("resumes/resume_john_doe.pdf")

assert r["success"] is True

assert "page_count" in r["metadata"]

# DOCX

r = read_file("resumes/resume_jane_smith.docx")

assert r["success"] is True

# Missing file

r = read_file("resumes/ghost.pdf")

assert r["success"] is False

assert "FileNotFoundError" in r["error"]

# Unsupported format

r = read_file("resumes/resume_alice_wang.txt".replace(".txt", ".xyz"))

# (rename a temp copy first)

# Path traversal attempt

r = read_file("../../etc/passwd")

assert r["success"] is False

assert "Path not allowed" in r["error"]

```

### Exit Criteria

- All six smoke tests pass

- No uncaught exception leaks out of `read_file()` under any input

---

## Phase 2 — `list_files()` Tool

### Goal

Enumerate files in a directory, optionally filtering by extension. Returns an alphabetically sorted list of file-metadata dicts; returns `[]` gracefully when the directory is missing or empty.

### Files Touched

- `fs_tools.py`

### Implementation Steps

**2.1 — Core function**

```python

import logging

def list_files(directory: str, extension: str = None) -> list:

    try:

        if not os.path.isdir(directory):

            logging.warning("list_files: directory '%s' does not exist", directory)

            return []

        entries = []

        with os.scandir(directory) as it:

            for entry in it:

                if not [entry.is](http://entry.is)_file():

                    continue

                entry_ext = Path([entry.name](http://entry.name)).suffix.lower()

                # Extension filter (case-insensitive, accept ".pdf" or "pdf")

                if extension is not None:

                    wanted = extension if extension.startswith(".") else f".{extension}"

                    if entry_ext != wanted.lower():

                        continue

                stat = entry.stat()

                entries.append({

                    "filename": [entry.name](http://entry.name),

                    "filepath": os.path.join(directory, [entry.name](http://entry.name)),

                    "extension": entry_ext,

                    "size_bytes": [stat.st](http://stat.st)_size,

                    "modified_at": datetime.fromtimestamp(

                        [stat.st](http://stat.st)_mtime

                    ).isoformat(timespec="seconds"),

                })

        return sorted(entries, key=lambda e: e["filename"].lower())

    except Exception as e:

        logging.error("list_files error: %s", e)

        return []

```

### Manual Smoke Tests

```python

from fs_tools import list_files

# All files (mixed formats)

files = list_files("resumes")

assert len(files) == 3

exts = {f["extension"] for f in files}

assert exts == {".pdf", ".docx", ".txt"}

# Filtered to PDF only

pdfs = list_files("resumes", extension=".pdf")

assert all(f["extension"] == ".pdf" for f in pdfs)

# Case-insensitive extension match

same = list_files("resumes", extension="PDF")

assert len(same) == len(pdfs)

# Non-existent directory

empty = list_files("does_not_exist")

assert empty == []

# Each entry has all required keys

required_keys = {"filename", "filepath", "extension", "size_bytes", "modified_at"}

for f in files:

    assert required_keys.issubset(f.keys())

```

### Exit Criteria

- All five smoke tests pass

- Alphabetical sort is stable across multiple calls

- No exception leaks; returns `[]` on error

---

## Phase 3 — `write_file()` Tool

### Goal

Write UTF-8 text to a file, creating parent directories if needed. Security-check every target path against `OUTPUT_DIR` before writing. Return bytes written as confirmation.

### Files Touched

- `fs_tools.py`

### Implementation Steps

**3.1 — Core function**

```python

def write_file(filepath: str, content: str) -> dict:

    try:

        # Security gate — only allow writes inside output/

        if not *is*safe_write_path(filepath):

            return {"success": False, "filepath": filepath,

                    "error": "Path not allowed — writes are restricted to the output directory"}

        path = Path(filepath)

        dir_existed = path.parent.exists()

        os.makedirs(path.parent, exist_ok=True)

        encoded = content.encode("utf-8")

        with open(filepath, "w", encoding="utf-8") as f:

            f.write(content)

        return {

            "success": True,

            "filepath": filepath,

            "bytes_written": len(encoded),

            "created_dirs": not dir_existed,

        }

    except Exception as e:

        return {"success": False, "filepath": filepath, "error": str(e)}

```

### Manual Smoke Tests

```python

from fs_tools import write_file

import os

# Basic write

r = write_file("output/test.txt", "Hello, world!")

assert r["success"] is True

assert r["bytes_written"] == len("Hello, world!".encode("utf-8"))

# File actually exists

assert os.path.exists("output/test.txt")

# Directory auto-creation

r = write_file("output/subdir/nested.txt", "Nested content")

assert r["success"] is True

assert r["created_dirs"] is True

# Overwrite existing file

r = write_file("output/test.txt", "Overwritten")

assert r["success"] is True

# Path traversal attempt

r = write_file("../../etc/cron.d/evil", "rm -rf /")

assert r["success"] is False

assert "Path not allowed" in r["error"]

```

### Exit Criteria

- All five smoke tests pass

- Path traversal is blocked at every attempt

- Bytes-written count matches the UTF-8 byte length of content

---

## Phase 4 — `search_in_file()` Tool

### Goal

Search a file for a keyword or multi-word phrase. Reuse `read_file()` internally for text extraction. Return all case-insensitive matches with ±100-character context snippets.

### Files Touched

- `fs_tools.py`

### Implementation Steps

**4.1 — Context extractor helper**

```python

def *extract*context(text: str, match, window: int = 100) -> str:

    start = max(0, match.start() - window)

    end = min(len(text), match.end() + window)

    snippet = text[start:end]

    if start > 0:

        snippet = "..." + snippet

    if end < len(text):

        snippet = snippet + "..."

    return snippet

```

**4.2 — Core function**

```python

def search_in_file(filepath: str, keyword: str) -> dict:

    read_result = read_file(filepath)

    if not read_result["success"]:

        # Propagate the read error cleanly

        return {

            "success": False,

            "filepath": filepath,

            "keyword": keyword,

            "error": read_result["error"],

        }

    text = read_result["content"]

    pattern = re.compile(re.escape(keyword), re.IGNORECASE)

    matches_found = []

    for i, m in enumerate(pattern.finditer(text)):

        matches_found.append({

            "match_index": i,

            "matched_text": [m.group](http://m.group)(0),

            "context": *extract*context(text, m),

        })

    return {

        "success": True,

        "filepath": filepath,

        "keyword": keyword,

        "match_count": len(matches_found),

        "matches": matches_found,

    }

```

### Manual Smoke Tests

```python

from fs_tools import search_in_file

# Keyword present — case-insensitive

r = search_in_file("resumes/resume_john_doe.pdf", "python")

assert r["success"] is True

assert r["match_count"] >= 1

assert "context" in r["matches"][0]

# Multi-word phrase

r = search_in_file("resumes/resume_alice_wang.txt", "machine learning")

assert r["success"] is True  # or match_count == 0 if not present

# Keyword absent — returns zero matches, not an error

r = search_in_file("resumes/resume_alice_wang.txt", "xyzzy_not_found_12345")

assert r["success"] is True

assert r["match_count"] == 0

assert r["matches"] == []

# Missing file — error propagated from read_file

r = search_in_file("resumes/ghost.pdf", "python")

assert r["success"] is False

assert "error" in r

# Context window contains keyword

r = search_in_file("resumes/resume_alice_wang.txt", "experience")

if r["match_count"] > 0:

    assert "experience" in r["matches"][0]["context"].lower()

```

### Exit Criteria

- All five smoke tests pass

- No duplicate matches on the same keyword occurrence

- `read_file()` is not duplicated; `search_in_file()` always calls it internally

---

## Phase 5 — LLM Tool Schemas

### Goal

Define the JSON Schema objects for all four tools in `llm_file_assistant.py`. These objects are passed directly to the LLM API on every request and determine whether the LLM can call the right tool with the right arguments.

### Files Touched

- `llm_file_assistant.py`

### Implementation Steps

**5.1 — Schema registry constant**

```python

# llm_file_[assistant.py](http://assistant.py)

TOOL_SCHEMAS = [

    {

        "type": "function",

        "function": {

            "name": "read_file",

            "description": (

                "Read a resume file (PDF, TXT, or DOCX) and return its "

                "plain-text content along with file metadata."

            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "filepath": {

                        "type": "string",

                        "description": "Absolute or relative path to the file to read.",

                    }

                },

                "required": ["filepath"],

            },

        },

    },

    {

        "type": "function",

        "function": {

            "name": "list_files",

            "description": (

                "List all files in a directory. "

                "Optionally filter by extension such as .pdf, .txt, or .docx."

            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "directory": {

                        "type": "string",

                        "description": "Absolute or relative path to the directory to scan.",

                    },

                    "extension": {

                        "type": "string",

                        "description": (

                            "Optional extension filter, e.g. '.pdf'. "

                            "Omit to return all file types."

                        ),

                    },

                },

                "required": ["directory"],

            },

        },

    },

    {

        "type": "function",

        "function": {

            "name": "write_file",

            "description": (

                "Write UTF-8 text content to a file. "

                "Parent directories are created automatically if they do not exist."

            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "filepath": {

                        "type": "string",

                        "description": "Target path for the file to create or overwrite.",

                    },

                    "content": {

                        "type": "string",

                        "description": "The full text content to write into the file.",

                    },

                },

                "required": ["filepath", "content"],

            },

        },

    },

    {

        "type": "function",

        "function": {

            "name": "search_in_file",

            "description": (

                "Search a file for a keyword or phrase. "

                "Returns all case-insensitive matches with surrounding context."

            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "filepath": {

                        "type": "string",

                        "description": "Absolute or relative path to the file to search.",

                    },

                    "keyword": {

                        "type": "string",

                        "description": "Keyword or multi-word phrase to search for.",

                    },

                },

                "required": ["filepath", "keyword"],

            },

        },

    },

]

```

**5.2 — Schema validation smoke test**

```python

import json

from llm_file_assistant import TOOL_SCHEMAS

assert len(TOOL_SCHEMAS) == 4

names = {t["function"]["name"] for t in TOOL_SCHEMAS}

assert names == {"read_file", "list_files", "write_file", "search_in_file"}

# Every schema must have a description and required fields list

for schema in TOOL_SCHEMAS:

    fn = schema["function"]

    assert fn.get("description"), f"{fn['name']} missing description"

    assert "parameters" in fn

    assert "required" in fn["parameters"]

print("TOOL_SCHEMAS: OK")

```

### Exit Criteria

- Four schemas present, each with name, description, parameters, and required fields

- `list_files.extension` is not in required (it is optional)

- Schema validates against the Groq / OpenAI-compatible tool-calling spec format

---

## Phase 6 — Agentic Orchestration Loop

### Goal

Build `llm_file_assistant.py` around the schemas from Phase 5. Implement:

1. Config loader (reads `.env`)

2. Tool dispatcher (routes `tool_call.name` → `fs_tools.py` function)

3. Agentic loop `run_agent_loop`) that sends messages, handles tool calls, and terminates on `stop`

4. CLI entry point

### Files Touched

- `llm_file_assistant.py`

### Implementation Steps

**6.1 — Imports and config**

```python

import os

import json

import logging

from dotenv import load_dotenv

import fs_tools

load_dotenv()

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower()

MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

def build_llm_client():

    """Return the configured provider client. Default is Groq (OpenAI-compatible API)."""

    if LLM_PROVIDER == "groq":

        from openai import OpenAI

        return OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )

    if LLM_PROVIDER == "openai":

        from openai import OpenAI

        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    if LLM_PROVIDER == "anthropic":

        from anthropic import Anthropic

        return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

CLIENT = build_llm_client()

SYSTEM_PROMPT = """You are a resume assistant with access to file system tools.

Use the tools to read, list, search, and write files as directed.

When asked to summarise a resume, read it first, compose the summary yourself,

then write it to output/<filename_without_ext>_summary.txt."""

```

**6.2 — Tool dispatcher**

```python

TOOL_REGISTRY = {

    "read_file":      lambda args: fs_[tools.read](http://tools.read)_file(**args),

    "list_files":     lambda args: fs_tools.list_files(**args),

    "write_file":     lambda args: fs_tools.write_file(**args),

    "search_in_file": lambda args: fs_[tools.search](http://tools.search)_in_file(**args),

}

def dispatch_tool_call(name: str, arguments: dict) -> str:

    """Execute a tool and return its result as a JSON string for the LLM."""

    if name not in TOOL_REGISTRY:

        result = {"success": False, "error": f"Unknown tool: {name}"}

    else:

        try:

            result = TOOL_REGISTRY[name](arguments)

        except Exception as e:

            result = {"success": False, "error": str(e)}

    return json.dumps(result)

```

**6.3 — Agentic loop**

```python

MAX_ITERATIONS = 10  # guard against infinite loops

def create_llm_response(messages: list[dict]):

    """Provider adapter so the orchestration loop is not hardwired to one SDK."""

    if LLM_PROVIDER in ("groq", "openai"):

        return CLIENT.chat.completions.create(

            model=MODEL,

            messages=messages,

            tools=TOOL_SCHEMAS,

            tool_choice="auto",

        )

    if LLM_PROVIDER == "anthropic":

        raise NotImplementedError("Add the Anthropic messages API adapter here")

    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

def run_agent_loop(user_query: str) -> str:

    messages = [

        {"role": "system", "content": SYSTEM_PROMPT},

        {"role": "user",   "content": user_query},

    ]

    for iteration in range(MAX_ITERATIONS):

        response = create_llm_response(messages)

        choice = response.choices[0]

        # ── LLM is done ──────────────────────────────────────────────────

        if choice.finish_reason == "stop":

            return choice.message.content

        # ── LLM wants to call tools ───────────────────────────────────────

        if choice.finish_reason == "tool_calls":

            # 1. append the assistant message (which contains the tool_calls)

            messages.append(choice.message)

            # 2. execute each tool call and append results

            for tool_call in choice.message.tool_calls:

                name      = tool_[call.function.name](http://call.function.name)

                arguments = json.loads(tool_call.function.arguments)

                result    = dispatch_tool_call(name, arguments)

                messages.append({

                    "role":         "tool",

                    "tool_call_id": tool_[call.id](http://call.id),

                    "content":      result,

                })

    return "Max iterations reached without a final answer."

```

**6.4 — CLI entry point**

```python

def main():

    print("Resume Assistant — type 'quit' to exit\n")

    while True:

        try:

            query = input("You: ").strip()

        except (EOFError, KeyboardInterrupt):

            break

        if query.lower() in {"quit", "exit"}:

            break

        if not query:

            continue

        answer = run_agent_loop(query)

        print(f"\nAssistant: {answer}\n")

if **name** == "__main__":

    main()

```

### Exit Criteria

- `run_agent_loop("list the files in the resumes folder")` returns a non-empty string without raising

- The loop terminates naturally on `finish_reason == "stop"`

- `MAX_ITERATIONS` prevents any infinite tool-call cycles

---

## Phase 7 — End-to-End Validation

### Goal

Verify all three example queries from the original problem statement work correctly against real files.

### Files Touched

- read-only test run against all source files

### Test Script

Create a temporary `test_e2e.py` at the project root (delete after validation):

```python

# test_[e2e.py](http://e2e.py)  — run once to validate, then delete

from llm_file_assistant import run_agent_loop

SEP = "-" * 60

# ── Query 1: Read all resumes ───────────────────────────────────────────────

print(SEP)

print("Q1: Read all resumes in the resumes folder")

answer = run_agent_loop("Read all resumes in the resumes folder")

print(answer)

assert any(name in answer.lower() for name in ["john", "jane", "alice"]), \

    "Q1: expected candidate names in answer"

# ── Query 2: Find resumes mentioning Python ─────────────────────────────────

print(SEP)

print("Q2: Find resumes mentioning Python experience")

answer = run_agent_loop("Find resumes mentioning Python experience")

print(answer)

# The answer should reference at least file names or 'no matches'

assert isinstance(answer, str) and len(answer) > 20, "Q2: answer too short"

# ── Query 3: Create a summary file ─────────────────────────────────────────

import os

print(SEP)

print("Q3: Create a summary file for resume_john_doe.pdf")

answer = run_agent_loop("Create a summary file for resume_john_doe.pdf")

print(answer)

assert os.path.exists("output/summary_john_doe.txt"), \

    "Q3: expected output/summary_john_doe.txt to be created"

with open("output/summary_john_doe.txt") as f:

    summary_content = [f.read](http://f.read)()

assert len(summary_content) > 50, "Q3: summary file looks too short"

print(SEP)

print("All end-to-end tests passed.")

```

**Run it:**

```bash

python test_[e2e.py](http://e2e.py)

```

### Acceptance Criteria per Query

| Query | Must Pass |

|-------|-----------|

| "Read all resumes in the resumes folder" | LLM reads PDF, DOCX, and TXT files and synthesizes a response mentioning all three candidates |

| "Find resumes mentioning Python experience" | LLM calls `search_in_file` for each file; response lists which resumes matched or explicitly states none do |

| "Create a summary file for resume_john_doe.pdf" | `output/summary_john_doe.txt` exists; content is >50 chars; response confirms success |

---

## Phase 7b — Manual Testing Frontend (Web UI)

### Goal

Provide a simple browser UI so you can run the three example queries (and custom ones) without using the CLI.

### Files

| File | Purpose |
|------|---------|
| `web_app.py` | Flask server exposing `/api/chat`, `/api/resumes`, `/api/output` |
| `frontend/static/index.html` | Chat UI with example-query buttons |
| `frontend/static/style.css` | Basic styling |
| `frontend/static/app.js` | Fetch API client |

### Steps

**7b.1 Install Flask** (included in `requirements.txt`)

```bash
pip install -r requirements.txt
```

**7b.2 Start the server**

```bash
python web_app.py
```

Open **http://127.0.0.1:5000** in your browser.

**7b.3 Manual checks**

- Status bar shows Groq provider and that `GROQ_API_KEY` is configured
- Click each example query button; response appears in the Response panel
- Resumes and Output file lists refresh after each successful chat
- Q3 creates `output/summary_john_doe.txt` (visible under Output)

### Exit Criteria

- UI loads without errors
- `/api/chat` returns assistant answers for custom and example queries
- File lists reflect `resumes/` and `output/` contents

---

## Common Pitfalls & Fixes

| Symptom | Likely Cause | Fix |

|---------|-------------|-----|

| `pdfplumber` returns empty string | Scanned/image-only PDF | Use sample text-layer PDFs; `read_file` returns informative error |

| LLM never calls a tool | Schema `type: "function"` wrapper missing | Wrap each schema as shown in Phase 5 step 5.1 |

| `write_file` blocked on valid path | Paths are resolved from the process cwd or checked with raw string prefixes | Anchor `RESUMES_DIR` and `OUTPUT_DIR` to `Path(__file__).resolve().parent` and use `Path.relative_to()`-style containment checks |

| Tool call loop never stops | LLM keeps calling tools | Ensure `MAX_ITERATIONS` guard is in place; check system prompt |

| `search_in_file` returns wrong match count | `re.escape()` missing | Always escape keyword before compiling pattern |

| DOCX paragraphs include empty runs | Header/footer whitespace | Filter with `if p.text.strip()` as shown in Phase 1 |

---

## Final Checklist

- [ ] Phase 0 — scaffold complete, dependencies installed, sample files in place

- [ ] Phase 1 — `read_file()` handles PDF, DOCX, TXT; all error paths return `success: false`

- [ ] Phase 2 — `list_files()` filters by extension; returns `[]` for missing dir

- [ ] Phase 3 — `write_file()` rejects paths outside `output/`; creates dirs; returns `bytes_written`

- [ ] Phase 4 — `search_in_file()` uses `read_file()` internally; returns context snippets

- [ ] Phase 5 — four schemas in `TOOL_SCHEMAS`; `list_files.extension` is optional

- [ ] Phase 6 — agentic loop handles `tool_calls` and `stop` finish reasons; `MAX_ITERATIONS` guard in place

- [ ] Phase 7 — all three example queries pass end-to-end; `output/summary_john_doe.txt` created
- [ ] Phase 7b — web UI runs at http://127.0.0.1:5000 for manual testing