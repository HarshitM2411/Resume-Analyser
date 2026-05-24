# Project Context: LLM-Powered File System Assistant

## Overview

This project involves building a two-part Python system that combines file system tooling with a Large Language Model (LLM) to create an intelligent assistant capable of reading, searching, and summarizing resume files through natural language queries.

---

## Part A: Core File System Tools `fs_tools.py`)

### Purpose

`fs_tools.py` is a standalone utility module that exposes four core tools for interacting with the local file system. These tools are designed to be LLM-callable (i.e., defined with structured schemas for function/tool calling) and should handle all I/O operations gracefully.

---

### Tool 1: `read_file(filepath: str) → dict`

**Responsibility:** Read the content of a resume file from disk and return structured data.

**Supported Formats:**

| Format | Library | Notes |

|--------|---------|-------|

| `.txt` | Built-in `open()` | UTF-8 encoding |

| `.pdf` | `PyPDF2` or `pdfplumber` | Extract text from all pages |

| `.docx` | `python-docx` | Extract paragraph text |

**Return Schema:**

```json

{

  "success": true,

  "filepath": "/path/to/file.pdf",

  "format": "pdf",

  "content": "Extracted plain text...",

  "metadata": {

    "filename": "resume_john_doe.pdf",

    "size_bytes": 45231,

    "page_count": 2,         // PDF only

    "word_count": 412,

    "modified_at": "2026-05-20T10:32:00"

  }

}

```

**Error Response:**

```json

{

  "success": false,

  "filepath": "/path/to/file.pdf",

  "error": "FileNotFoundError: No such file or directory"

}

```

**Key Considerations:**

- Normalize extracted text (strip excessive whitespace, handle encoding issues)

- For PDFs with no extractable text (scanned/image-based), return an informative error rather than an empty string

- Do not raise exceptions — catch all errors and return them in the response dict

---

### Tool 2: `list_files(directory: str, extension: str = None) → list`

**Responsibility:** Enumerate files in a given directory, optionally filtered by file extension.

**Parameters:**

- `directory` — absolute or relative path to a folder

- `extension` — optional filter, e.g. `".pdf"`, `".txt"`, `".docx"` (case-insensitive match)

**Return Schema:**

```json

[

  {

    "filename": "resume_jane_smith.pdf",

    "filepath": "/resumes/resume_jane_smith.pdf",

    "extension": ".pdf",

    "size_bytes": 38120,

    "modified_at": "2026-05-18T14:05:22"

  }

]

```

**Returns an empty list `[]` if:**

- Directory is empty

- No files match the given extension

- Directory does not exist (also log a warning)

**Key Considerations:**

- Non-recursive by default (only top-level files); optionally support `recursive=True`

- Sort results by filename alphabetically for consistent output

- Normalize extension matching: `.PDF` and `.pdf` should both match

---

### Tool 3: `write_file(filepath: str, content: str) → dict`

**Responsibility:** Write text content to a file at the specified path.

**Behavior:**

- If the target directory does not exist, create it (using `os.makedirs`)

- If the file already exists, overwrite it

- Write content using UTF-8 encoding

**Return Schema:**

```json

{

  "success": true,

  "filepath": "/output/summary_john_doe.txt",

  "bytes_written": 1024,

  "created_dirs": true

}

```

**Error Response:**

```json

{

  "success": false,

  "filepath": "/output/summary_john_doe.txt",

  "error": "PermissionError: Access denied"

}

```

**Key Considerations:**

- Avoid writing to sensitive system paths — validate that the path is within the working directory or a known safe directory

- Return the number of bytes actually written as confirmation

- Do not silently truncate content

---

### Tool 4: `search_in_file(filepath: str, keyword: str) → dict`

**Responsibility:** Search for a keyword or phrase within a file's text content and return matches with surrounding context.

**Behavior:**

- Case-insensitive search

- Extract a context window (e.g., 100 characters before and after each match)

- Deduplicate overlapping matches on the same line

**Return Schema:**

```json

{

  "success": true,

  "filepath": "/resumes/resume_john_doe.pdf",

  "keyword": "Python",

  "match_count": 3,

  "matches": [

    {

      "match_index": 0,

      "matched_text": "Python",

      "context": "...5 years of experience with Python and Django frameworks, building..."

    }

  ]

}

```

**Returns `match_count: 0` and empty `matches: []` when keyword is not found.**

**Key Considerations:**

- Internally calls `read_file()` to extract text before searching

- Use `re.finditer()` with `re.IGNORECASE` for robust matching

- Keyword can be a multi-word phrase (e.g., `"machine learning"`)

---

## Part B: LLM Integration `llm_file_assistant.py`)

### Purpose

`llm_file_assistant.py` wraps the tools from `fs_tools.py` and exposes them to an LLM via its native function/tool-calling interface. The LLM decides which tools to call based on a user's natural language query, and the assistant orchestrates the execution loop.

---

### Architecture: Agentic Tool-Calling Loop

```

User Query

    │

    ▼

LLM (with tool schemas)

    │

    ├── Decides to call tool(s)

    │         │

    │         ▼

    │   Tool execution (fs_[tools.py](http://tools.py))

    │         │

    │         ▼

    │   Tool result returned to LLM

    │

    └── LLM generates final natural language response

            │

            ▼

        User sees answer

```

This is a **ReAct-style loop**: the LLM reasons, acts (calls a tool), observes the result, and repeats until it has enough information to respond.

---

### LLM Tool Schema Definitions

Each tool must be described in JSON Schema format for the LLM API. Example for `read_file`:

```json

{

  "name": "read_file",

  "description": "Read a resume file (PDF, TXT, or DOCX) and return its text content and metadata.",

  "parameters": {

    "type": "object",

    "properties": {

      "filepath": {

        "type": "string",

        "description": "Absolute or relative path to the file to read."

      }

    },

    "required": ["filepath"]

  }

}

```

All four tools need explicit schema definitions. A complete set is shown below.

```json

[

  {

    "name": "read_file",

    "description": "Read a resume file (PDF, TXT, or DOCX) and return its text content and metadata.",

    "parameters": {

      "type": "object",

      "properties": {

        "filepath": {

          "type": "string",

          "description": "Absolute or relative path to the file to read."

        }

      },

      "required": ["filepath"]

    }

  },

  {

    "name": "list_files",

    "description": "List files in a directory and optionally filter them by extension.",

    "parameters": {

      "type": "object",

      "properties": {

        "directory": {

          "type": "string",

          "description": "Absolute or relative path to the directory to scan."

        },

        "extension": {

          "type": "string",

          "description": "Optional extension filter such as .pdf, .txt, or .docx.",

          "nullable": true

        }

      },

      "required": ["directory"]

    }

  },

  {

    "name": "write_file",

    "description": "Write UTF-8 text content to a file, creating parent directories when needed.",

    "parameters": {

      "type": "object",

      "properties": {

        "filepath": {

          "type": "string",

          "description": "Target path for the file to create or overwrite."

        },

        "content": {

          "type": "string",

          "description": "Text content to write into the file."

        }

      },

      "required": ["filepath", "content"]

    }

  },

  {

    "name": "search_in_file",

    "description": "Search a file for a keyword or phrase and return case-insensitive matches with context.",

    "parameters": {

      "type": "object",

      "properties": {

        "filepath": {

          "type": "string",

          "description": "Absolute or relative path to the file to search."

        },

        "keyword": {

          "type": "string",

          "description": "Keyword or phrase to search for inside the file content."

        }

      },

      "required": ["filepath", "keyword"]

    }

  }

]

```

---

### Supported LLM Providers

| Provider | Model Example | Tool Calling API |

|----------|--------------|-----------------|

| OpenAI | `gpt-4o` | `tools` parameter in Chat Completions |

| Anthropic | `claude-3-5-sonnet` | `tools` parameter in Messages API |

| Groq | `llama3-groq-tool-use-8b` | OpenAI-compatible `tools` parameter |

The implementation should default to **one provider** but be structured so the provider can be swapped by changing a config value or environment variable.

---

### Example Query Flows

#### Query 1: "Read all resumes in the resumes folder"

1. LLM calls `list_files(directory="resumes")`

2. Receives a mixed-format list of resume files, such as PDF, DOCX, and TXT

3. LLM calls `read_file()` for each file (sequentially or in parallel)

4. LLM synthesizes results into a summary response

#### Query 2: "Find resumes mentioning Python experience"

1. LLM calls `list_files(directory="resumes")`

2. For each file, LLM calls `search_in_file(filepath=..., keyword="Python")`

3. LLM collects files with `match_count > 0`

4. LLM responds with names of matching candidates and match excerpts

#### Query 3: "Create a summary file for resume_john_doe.pdf"

1. LLM calls `read_file(filepath="resumes/resume_john_doe.pdf")`

2. LLM internally generates a summary of the content using the extracted text from `read_file()`

3. LLM calls `write_file(filepath="output/summary_john_doe.txt", content="...")`

4. LLM confirms the file was written successfully

### Summary Generation Notes

- The LLM, not `fs_tools.py`, is responsible for turning extracted resume text into a natural-language summary.

- `fs_tools.py` provides the read and write primitives only; it does not perform summarization itself.

- The assistant should keep generated summaries concise, factual, and grounded in the extracted resume content before calling `write_file()`.

---

## Project Structure

```

airTribe LLM Project/

├── docs/

│   └── [context.md](http://context.md)               ← this file

├── resumes/                     ← sample input files

│   ├── resume_john_doe.pdf

│   ├── resume_jane_smith.docx

│   └── resume_alice_wang.txt

├── output/                      ← generated summaries land here

├── fs_[tools.py](http://tools.py)                  ← Part A: file system tools

├── llm_file_[assistant.py](http://assistant.py)        ← Part B: LLM + tool orchestration

├── requirements.txt

└── .env                         ← API keys (never commit this)

```

---

## Dependencies

```

# requirements.txt

openai>=1.0.0          # or anthropic>=0.20.0

pdfplumber             # PDF text extraction

python-docx            # DOCX text extraction

python-dotenv          # Load API keys from .env

```

---

## Environment Variables `.env`)

```

OPENAI_API_KEY=sk-...

# OR

ANTHROPIC_API_KEY=sk-ant-...

LLM_PROVIDER=openai           # openai | anthropic | groq

LLM_MODEL=gpt-4o

RESUMES_DIR=./resumes

OUTPUT_DIR=./output

```

---

## Error Handling Philosophy

- **All tools return dicts, never raise exceptions to the caller.** Errors are captured and returned as `{"success": false, "error": "..."}`.

- The LLM assistant layer should detect `success: false` in tool results and inform the user clearly rather than silently failing.

- File I/O errors, unsupported formats, missing files, and permission errors must all be handled.

---

## Security Considerations

- **Path traversal prevention:** Validate that all file paths resolve within the allowed working directory. Reject paths containing `../` sequences that escape the project root.

- **API key safety:** Keys must only be loaded from environment variables `.env`). Never hardcode keys in source files.

- **Output directory isolation:** `write_file` should only write to the designated `output/` directory unless explicitly configured otherwise.

---

## Evaluation Criteria Summary

| Area | Weight | Key Checkpoints |

|------|--------|----------------|

| `fs_tools.py` — all 4 tools implemented | 60% | Correct return schemas, error handling, format support |

| `llm_file_assistant.py` — LLM integration | 40% | Tool schemas defined, agentic loop works, example queries run end-to-end |

---

## Suggested Implementation Order

1. Implement and unit-test `read_file()` for all three formats

2. Implement `list_files()` with extension filtering

3. Implement `write_file()` with directory creation

4. Implement `search_in_file()` using `read_file()` internally

5. Define JSON tool schemas for all four tools

6. Build the LLM assistant loop in `llm_file_assistant.py`

7. Test all three example query flows end-to-end