# Evaluation Criteria

## LLM-Powered File System Assistant — Per-Phase Rubric

> Each phase must satisfy **all** Exit Criteria before proceeding to the next.  

> Grading follows the 60/40 split from `context.md`: Part A tools (Phases 1–4) = 60%, Part B orchestration (Phases 5–6) = 40%, Phase 7 validation = overall acceptance.

---

## Phase 0 — Project Scaffold

### Pass / Fail Gate (must be all green before Phase 1)

| Check | How to Verify | Pass Condition |

|-------|--------------|----------------|

| Dependencies install cleanly | `pip install -r requirements.txt` | No errors; no version conflicts |

| All three libraries importable | `python -c "import pdfplumber, docx, openai, dotenv; print('OK')"` | Prints `OK` |

| `.env` file present and parseable | `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('LLM_PROVIDER'))"` | Prints provider name, not `None` |

| Sample files exist | `ls resumes/` | At least one `.pdf`, one `.docx`, one `.txt` |

| `.gitignore` covers secrets | `cat .gitignore` | `.env` and `output/` both listed |

| Source file stubs created | `ls fs_tools.py llm_file_assistant.py` | Both files exist |

### Grading

- **100%** — All 6 checks pass  

- **0%** — Any check fails (blocked; cannot proceed)

---

## Phase 1 — `read_file()`

> **Weight**: Part A — contributes to the 60% Part A score.

### Functional Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| TXT reads correctly | `read_file("resumes/resume_alice_wang.txt")` | `success: true`, `content` non-empty, `format: "txt"` |

| PDF reads correctly | `read_file("resumes/resume_john_doe.pdf")` | `success: true`, `"page_count"` in `metadata` |

| DOCX reads correctly | `read_file("resumes/resume_jane_smith.docx")` | `success: true`, `content` contains paragraph text |

| Metadata complete | Any successful read | `filename`, `size_bytes`, `word_count`, `modified_at` all present |

| Text normalised | Check for 3+ consecutive newlines or multiple spaces | None present in `content` |

### Error Handling Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Missing file | `read_file("resumes/ghost.pdf")` | `success: false`, `"FileNotFoundError"` in `error` |

| Unsupported format | `read_file("resumes/resume.xyz")` | `success: false`, `"UnsupportedFormat"` in `error` |

| Scanned PDF | `read_file` on a PDF with no text layer | `success: false`, `"Scanned PDF"` in `error` |

| Path traversal | `read_file("../../etc/passwd")` | `success: false`, `"Path not allowed"` in `error` |

| Symlink escape | `read_file` on a symlink pointing outside project | `success: false`, `"Path not allowed"` in `error` |

| No exception leaks | Call `read_file` with any malformed input | Function always returns a dict; never raises to caller |

### Scoring

| Score | Criteria |

|-------|----------|

| **Full credit** | All 5 functional + all 6 error handling checks pass |

| **Partial (80%)** | All 5 functional pass; ≥4 error handling pass |

| **Partial (50%)** | TXT + DOCX functional pass; PDF partial; ≥3 error handling pass |

| **No credit** | Any functional check fails OR any exception leaks out |

---

## Phase 2 — `list_files()`

> **Weight**: Part A — contributes to the 60% Part A score.

### Functional Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Lists all files | `list_files("resumes")` | Returns 3 dicts with all required keys |

| Required keys present | Inspect each entry | `filename`, `filepath`, `extension`, `size_bytes`, `modified_at` all present |

| Alphabetical sort | `[f["filename"] for f in list_files("resumes")]` | List is sorted case-insensitively A→Z |

| Extension filter (with dot) | `list_files("resumes", extension=".pdf")` | Returns only `.pdf` entries |

| Extension filter (without dot) | `list_files("resumes", extension="pdf")` | Same result as `.pdf` filter |

| Case-insensitive extension | `list_files("resumes", extension="PDF")` | Returns same count as `".pdf"` |

### Error Handling Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Non-existent directory | `list_files("does_not_exist")` | Returns `[]`, no exception |

| Empty directory | `list_files` on a newly created empty dir | Returns `[]` |

| Directory with only subdirs | Place no files in a dir; call `list_files` | Returns `[]` |

| Stable sort | Call `list_files("resumes")` three times | Identical order every time |

### Scoring

| Score | Criteria |

|-------|----------|

| **Full credit** | All 6 functional + all 4 error handling checks pass |

| **Partial (75%)** | All functional pass; 3/4 error handling pass |

| **No credit** | Any functional check fails OR exception leaks |

---

## Phase 3 — `write_file()`

> **Weight**: Part A — contributes to the 60% Part A score.

### Functional Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Basic write | `write_file("output/test.txt", "Hello")` | `success: true`; `os.path.exists("output/test.txt")` |

| Byte count accurate | Compare `r["bytes_written"]` to `len("Hello".encode("utf-8"))` | Values are equal |

| Auto-creates directories | `write_file("output/a/b/c.txt", "x")` | `success: true`; `created_dirs: true` |

| Overwrites existing file | Write same path twice with different content | Second write returns `success: true`; file contains new content |

| Unicode content | `write_file("output/uni.txt", "Résumé 🧑‍💻")` | File readable with UTF-8 encoding; byte count matches |

### Security Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Path traversal blocked | `write_file("../../etc/cron.d/evil", "x")` | `success: false`, `"Path not allowed"` |

| Sibling directory blocked | `write_file("output_backup/evil.txt", "x")` | `success: false`, `"Path not allowed"` |

| Write to `resumes/` blocked | `write_file("resumes/injected.txt", "x")` | `success: false`, `"Path not allowed"` |

| Absolute path to allowed dir | `write_file("/abs/path/to/output/ok.txt", "x")` | Allowed if path resolves inside `output/`; blocked otherwise |

### Scoring

| Score | Criteria |

|-------|----------|

| **Full credit** | All 5 functional + all 4 security checks pass |

| **Partial (70%)** | All functional pass; 3/4 security pass |

| **No credit** | Any security check allows a path outside `output/`, OR any functional check fails |

---

## Phase 4 — `search_in_file()`

> **Weight**: Part A — contributes to the 60% Part A score.

### Functional Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Keyword present | Search for a word known to be in a TXT resume | `success: true`, `match_count >= 1` |

| Case-insensitive match | Search `"python"` when file contains `"Python"` | Match found |

| Multi-word phrase | Search `"machine learning"` | Returns matches if present; `match_count: 0` if absent; never errors |

| Context window present | Check `matches[0]["context"]` | Non-empty string containing the matched keyword |

| Context includes keyword | `keyword.lower() in matches[0]["context"].lower()` | True |

| Keyword absent | Search for `"xyzzy_not_found_12345"` | `success: true`, `match_count: 0`, `matches: []` |

| Delegates to `read_file` | Inspect source code | No file-open logic duplicated; calls `read_file()` internally |

### Error Handling Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Missing file | `search_in_file("ghost.pdf", "python")` | `success: false`, error propagated from `read_file` |

| Regex special chars in keyword | `search_in_file(file, "C++")` | Does not raise `re.error`; matches literal `"C++"` |

| Empty keyword | `search_in_file(file, "")` | Either graceful `match_count: 0` or `success: false` with a validation error — must not return thousands of empty-string matches |

### Scoring

| Score | Criteria |

|-------|----------|

| **Full credit** | All 7 functional + all 3 error handling checks pass |

| **Partial (70%)** | ≥5 functional pass; ≥2 error handling pass |

| **No credit** | `read_file` logic duplicated, OR exception leaks, OR `re.error` raised on special chars |

---

## Phase 5 — LLM Tool Schemas

> **Weight**: Part B — contributes to the 40% Part B score.

### Schema Structure Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Exactly 4 schemas | `len(TOOL_SCHEMAS) == 4` | True |

| Correct tool names | `{t["function"]["name"] for t in TOOL_SCHEMAS}` | `== {"read_file", "list_files", "write_file", "search_in_file"}` |

| OpenAI wrapper format | Each schema has `{"type": "function", "function": {...}}` | True for all 4 |

| All schemas have description | `fn.get("description")` for each | Truthy (non-empty string) |

| Required fields declared | `"required" in fn["parameters"]` for each | True |

| `list_files.extension` is optional | `"extension" not in list_files_schema["parameters"]["required"]` | True |

| `list_files.directory` is required | `"directory" in list_files_schema["parameters"]["required"]` | True |

### Integration Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| No circular import | `python -c "from llm_file_assistant import TOOL_SCHEMAS"` | No `ImportError`; no `CircularImportError` |

| TOOL_SCHEMAS referenced internally | `TOOL_SCHEMAS` used in `create_llm_response()` in the same file | No cross-file import of this constant |

### Scoring

| Score | Criteria |

|-------|----------|

| **Full credit** | All 7 schema structure + both integration checks pass |

| **Partial (60%)** | ≥5 schema checks pass; both integration checks pass |

| **No credit** | Circular import exists, OR fewer than 4 schemas, OR `list_files.extension` is marked required |

---

## Phase 6 — Agentic Orchestration Loop

> **Weight**: Part B — contributes to the 40% Part B score.

### Loop Behaviour Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| Simple query returns string | `run_agent_loop("list the files in the resumes folder")` | Returns non-empty `str`; no exception |

| Terminates on `stop` | Run a query the LLM can answer directly | `finish_reason == "stop"` ends the loop |

| Handles `tool_calls` correctly | Run a query that requires tool use | Tool called, result appended, LLM re-called, final answer returned |

| Multiple tool calls in one turn | Query that triggers parallel tool calls | All tool results appended before re-calling LLM |

| MAX_ITERATIONS guard | Inspect source | `MAX_ITERATIONS` constant defined; loop uses `range(MAX_ITERATIONS)` |

| MAX_ITERATIONS returns gracefully | (Simulate by setting MAX_ITERATIONS=1 and asking a complex question) | Returns `"Max iterations reached..."` instead of hanging |

### Dispatcher Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| All 4 tools dispatchable | Call `dispatch_tool_call` with each tool name | Returns a JSON string for each |

| Unknown tool handled | `dispatch_tool_call("nonexistent", {})` | Returns JSON with `success: false` and error message; no `KeyError` |

| Tool error propagated | Call a tool that returns `success: false` | JSON string appended to messages as `role: tool` content |

### Config / Provider Criteria

| Criterion | Measurable Test | Pass Condition |

|-----------|----------------|----------------|

| `build_llm_client()` factory used | Inspect source | Client built via `build_llm_client()`, not inline |

| `LLM_PROVIDER` drives client selection | Set `LLM_PROVIDER=unsupported` in `.env`; run | `ValueError` raised with message naming the unsupported provider |

| Missing API key gives clear error | Unset `OPENAI_API_KEY`; import module | `KeyError` with `"OPENAI_API_KEY"` — at least traceable; ideally a friendly message |

| `create_llm_response()` adapter present | Inspect source | All LLM call logic isolated in this function; `run_agent_loop` does not call SDK directly |

### Scoring

| Score | Criteria |

|-------|----------|

| **Full credit** | All 6 loop + all 3 dispatcher + all 4 config checks pass |

| **Partial (70%)** | All loop checks pass; ≥2 dispatcher + ≥2 config checks pass |

| **Partial (40%)** | Basic loop works; MAX_ITERATIONS guard missing; unknown tool crashes |

| **No credit** | `run_agent_loop` raises an exception on any valid query |

---

## Phase 7 — End-to-End Validation

> **Weight**: Overall acceptance gate. Failures here indicate integration issues even if individual phases passed.

### Query 1: "Read all resumes in the resumes folder"

| Criterion | Pass Condition |

|-----------|----------------|

| LLM calls `list_files` with `"resumes"` directory | Visible in message history or log |

| LLM calls `read_file` for each listed file | At least 3 `read_file` calls (one per format) |

| Final answer mentions all three candidates | At least two of: John, Jane, Alice (or their file names) |

| No uncaught exception in full run | `python test_e2e.py` exits with code 0 for Q1 block |

### Query 2: "Find resumes mentioning Python experience"

| Criterion | Pass Condition |

|-----------|----------------|

| LLM calls `search_in_file` for each resume | At least 3 `search_in_file` calls |

| Response correctly reflects which files match | Names matching resumes, or explicit "no resumes mention Python" |

| Case-insensitive match used | LLM keyword may be lowercase; match count still correct |

| Answer is substantive (>20 chars) | `len(answer) > 20` |

### Query 3: "Create a summary file for resume_john_doe.pdf"

| Criterion | Pass Condition |

|-----------|----------------|

| `read_file` called for the target file | Tool call present in message history |

| `write_file` called with path inside `output/` | `filepath` starts with `output/` |

| Output file exists after run | `os.path.exists("output/summary_john_doe.txt")` |

| Summary is substantive | `len(open("output/summary_john_doe.txt").read()) > 50` |

| Final response confirms success | Answer contains "summary" or "created" or "written" |

### Overall Acceptance Scoring

| Score | Criteria |

|-------|----------|

| **Full pass** | All 3 queries pass all their criteria |

| **Conditional pass** | Q1 + Q2 pass; Q3 creates file but content is borderline short |

| **Fail** | Any query raises an uncaught exception, OR the output file is not created for Q3 |

---

## Aggregate Scoring Summary

| Phase | Max Points | Part Weight |

|-------|-----------|-------------|

| Phase 0 — Scaffold | Gate (pass/fail) | — |

| Phase 1 — `read_file` | 25 | Part A (60%) |

| Phase 2 — `list_files` | 15 | Part A (60%) |

| Phase 3 — `write_file` | 15 | Part A (60%) |

| Phase 4 — `search_in_file` | 15 | Part A (60%) |

| Phase 5 — Tool schemas | 15 | Part B (40%) |

| Phase 6 — Agentic loop | 25 | Part B (40%) |

| Phase 7 — E2E queries | Acceptance gate | — |

> Part A total: Phases 1–4 = 70 points, weighted to 60% of final grade.  

> Part B total: Phases 5–6 = 40 points, weighted to 40% of final grade.  

> Phase 7 is a binary acceptance gate: all queries must pass for the project to be considered complete regardless of raw scores.