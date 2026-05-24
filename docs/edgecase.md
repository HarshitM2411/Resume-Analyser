# Edge Cases

## LLM-Powered File System Assistant

> Each section maps to a phase in `implementation.md`.  

> For every edge case: **Input → Expected Behaviour → Failure Mode if missed**.

---

## Phase 1 — `read_file()`

### PDF Edge Cases

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 1.1 | Scanned / image-only PDF (no text layer) | `success: false`, error `"Scanned PDF — no extractable text layer found"` | Returns `success: true` with empty `content`, silently passes bad data to LLM |

| 1.2 | PDF with only whitespace pages | `success: true`, `content` is empty string after normalization, `word_count: 0` | Downstream `search_in_file` returns 0 matches even for valid keywords |

| 1.3 | Encrypted / password-protected PDF | `success: false`, error from pdfplumber propagated into `error` field | Raises uncaught exception and crashes the tool call |

| 1.4 | Zero-byte PDF file | `success: false`, descriptive error | `pdfplumber` may return an empty page list; silently returns empty content |

| 1.5 | Multi-page PDF (10+ pages) | All pages concatenated, `page_count` reflects actual count | Only first page extracted if loop terminates early |

### DOCX Edge Cases

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 1.6 | DOCX with no paragraphs (only tables or images) | `success: true`, `content` is empty string | Raises `AttributeError` iterating `.paragraphs` |

| 1.7 | Corrupted / non-DOCX file renamed to `.docx` | `success: false`, error from `python-docx` propagated | Raises `BadZipFile` and crashes |

| 1.8 | DOCX with header/footer text only | `success: true`, paragraph text is empty after stripping — `content` may be empty | Header text leaked into content if `p.text.strip()` filter is missing |

| 1.9 | Very large DOCX (1000+ paragraphs) | All paragraphs joined, normalization applied | Memory pressure if entire text held in memory without streaming |

### TXT Edge Cases

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 1.10 | TXT file with non-UTF-8 encoding (Latin-1) | `success: false`, `UnicodeDecodeError` caught and returned | Hard crash; unhandled exception leaks to caller |

| 1.11 | Empty TXT file (0 bytes) | `success: true`, `content: ""`, `word_count: 0` | Crash if `split()` on empty string is not handled |

| 1.12 | TXT file with only whitespace / newlines | `success: true`, `content: ""` after normalization | Passes blank content as "valid" resume text to LLM |

| 1.13 | TXT file with Windows line endings `\r\n`) | Normalised to `\n`; no `\r` in output | `\r` characters remain in output and corrupt match positions in `search_in_file` |

### Path / Security Edge Cases

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 1.14 | `../../etc/passwd` | `success: false`, `"Path not allowed"` | Reads sensitive system files |

| 1.15 | `resumes/../../../etc/passwd` | `success: false` — `resolve()` expands the traversal first | Bypasses naive `..` string check |

| 1.16 | Symlink inside `resumes/` pointing outside project root | `success: false` — `resolve()` follows symlink to real path before checking | Symlink escape allows reads anywhere on the filesystem |

| 1.17 | File path with `~` (home dir expansion) | `success: false` — `expanduser().resolve()` used before containment check | `~/secret.txt` resolves outside project; naive check misses it |

| 1.18 | Absolute path within `resumes/`, e.g. `/Users/x/project/resumes/file.pdf` | `success: true` — absolute path that resolves inside allowed root is valid | Rejected incorrectly if check only allows relative paths |

---

## Phase 2 — `list_files()`

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 2.1 | Directory exists but is completely empty | Returns `[]`, no error or warning logged | `None` returned instead of `[]`; caller crashes on iteration |

| 2.2 | Directory does not exist | Returns `[]`, `logging.warning` emitted | `FileNotFoundError` raised; uncaught |

| 2.3 | Directory contains only subdirectories (no files) | Returns `[]` | Subdirectory entries incorrectly included in results |

| 2.4 | Extension filter `".PDF"` (uppercase) | Returns same results as `".pdf"` | No files returned when LLM passes uppercase extension |

| 2.5 | Extension filter `"pdf"` (no leading dot) | Normalised to `".pdf"`, returns matching files | Returns `[]` because `entry_ext` `.pdf`) never matches `"pdf"` |

| 2.6 | Directory contains a mix of `.pdf`, `.PDF`, `.Pdf` filenames | All three returned when filtering for `.pdf` | Case sensitivity on filename extensions causes misses |

| 2.7 | Directory contains a symlinked file | `entry.is_file()` returns `True` for symlinks to files; included in results | `is_file(follow_symlinks=False)` excludes symlinks; real files missed |

| 2.8 | `extension=""` (empty string) | Either treated as `None` (return all) or return only files with no extension — document the choice | Unpredictable silent filtering |

| 2.9 | Directory with 10,000+ files | Returns all matching files sorted; no crash | Memory exhaustion if entire dir is held before returning |

| 2.10 | Directory path contains trailing slash `"resumes/"` | Works identically to `"resumes"` | `os.path.isdir("resumes/")` returns `True`; `os.scandir` also works — low risk but confirm |

---

## Phase 3 — `write_file()`

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 3.1 | `output/../resumes/resume_john_doe.pdf` | `success: false`, path traversal blocked | Overwrites a source resume file |

| 3.2 | Sibling directory attack: `output_backup/evil.txt` | `success: false` — `output_backup` does not resolve inside `output/` | Raw `startswith("output")` prefix check incorrectly allows this path |

| 3.3 | Target directory does not exist `output/new_subdir/`) | Directory created automatically, file written | `FileNotFoundError`; `makedirs` not called before `open()` |

| 3.4 | Target file already exists | File overwritten silently | `success: false` returned incorrectly, or append instead of overwrite |

| 3.5 | Content containing non-ASCII / emoji `"Résumé 🧑‍💻"`) | Written and read back without corruption; `bytes_written` is byte count, not char count | Character count used instead of byte count; mismatch reported |

| 3.6 | Very large content string (1 MB+) | Written fully; `bytes_written` matches | Silent truncation if buffer limit hit; `bytes_written` incorrect |

| 3.7 | `filepath` with no parent directory component `"summary.txt"`) | Resolves to project root, fails containment check | Written to project root outside output/, bypassing the security gate |

| 3.8 | Read-only filesystem / permission denied | `success: false`, `PermissionError` caught and returned | Uncaught exception propagated to caller |

| 3.9 | Empty content string `""` | `success: true`, 0-byte file created, `bytes_written: 0` | Error raised if `makedirs` is not called for parent when `content` is empty |

---

## Phase 4 — `search_in_file()`

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 4.1 | Keyword with regex special chars `"C++"`, `"$100k"`, `"a.b"`) | `re.escape()` applied before compile; matches literal text only | `"a.b"` matches `"axb"`, `"a1b"` etc.; `"C++"` raises `re.error` |

| 4.2 | Keyword at the very start of the file (position 0) | `start = 0`; no leading `"..."` prepended | Negative slice index; `snippet = text[-100:]` wraps around incorrectly |

| 4.3 | Keyword at the very end of the file | `end = len(text)`; no trailing `"..."` appended | Index out of range |

| 4.4 | Keyword that matches on every line (e.g. `"the"` in a long resume) | Returns all matches with correct `match_index` values | Returns only first N matches if iteration is bounded |

| 4.5 | Keyword not present in file | `match_count: 0`, `matches: []`, `success: true` | `success: false` returned incorrectly as "error" |

| 4.6 | Empty keyword string `""` | `re.escape("")` compiles to a pattern matching every position; could return thousands of zero-width matches — should validate and reject | Thousands of empty-match entries flood the tool result and the LLM context window |

| 4.7 | Keyword longer than the entire file content | `match_count: 0`, `matches: []` | Index error when computing context window |

| 4.8 | File read fails (e.g. missing, corrupt, traversal blocked) | `success: false`, `error` propagated from `read_file()` | Raises `KeyError` accessing `read_result["content"]` when `success` is `False` |

| 4.9 | Multiple overlapping keyword occurrences on same line | Each non-overlapping match returned separately by `finditer` | Overlapping count mismatch if using `findall` instead of `finditer` |

| 4.10 | Keyword match at the context-window boundary (match spans exactly 100 chars from start) | Context correctly clipped to start of text with no negative index | Off-by-one error produces `"..."` on a window that starts at 0 |

---

## Phase 5 — LLM Tool Schemas

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 5.1 | LLM passes `filepath` as an integer instead of a string | `read_file(filepath=123)` — Python duck-types the int as a path; `Path(123)` raises `TypeError` caught by outer try/except | Hard crash if outer exception handler not present in dispatcher |

| 5.2 | LLM omits required `filepath` argument | `dispatch_tool_call` calls `fs_tools.read_file()` without `filepath`; `TypeError` caught and returned as `success: false` | Uncaught `TypeError` propagates to orchestrator |

| 5.3 | LLM passes extra unknown arguments `{"filepath": "...", "format": "pdf"}`) | `**args` unpacking raises `TypeError`; caught and returned as `success: false` | Unhandled `unexpected keyword argument` error |

| 5.4 | LLM passes `extension: null` for `list_files` | Python receives `None` from `json.loads`; `list_files(extension=None)` returns all files correctly | `None` check `extension.startswith(".")` raises `AttributeError` |

| 5.5 | `TOOL_SCHEMAS` not wrapped in `{"type": "function", "function": {...}}` outer dict | OpenAI API returns `400 Invalid tools` | LLM never calls any tool; silent empty responses |

---

## Phase 6 — Agentic Orchestration Loop

| # | Input | Expected Behaviour | Failure Mode if Missed |

|---|-------|--------------------|------------------------|

| 6.1 | LLM exceeds `MAX_ITERATIONS` without finishing | Loop exits, returns `"Max iterations reached without a final answer."` | Infinite loop; process hangs indefinitely |

| 6.2 | LLM calls an unknown tool name (not in `TOOL_REGISTRY`) | Dispatcher returns `{"success": false, "error": "Unknown tool: <name>"}` appended as a tool result | `KeyError` crashes the dispatcher |

| 6.3 | Tool returns `success: false` (e.g. file not found) | Error JSON returned to LLM as a `role: tool` message; LLM decides next action | Orchestrator silently discards error; LLM never knows and retries infinitely |

| 6.4 | LLM returns `finish_reason` other than `"stop"` or `"tool_calls"` (e.g. `"length"`, `"content_filter"`) | Loop iteration completes without acting; on next iteration LLM is re-called or `MAX_ITERATIONS` terminates | Unhandled `finish_reason` silently drops response; loop appears to hang |

| 6.5 | Empty user query `""` | Prompt sent to LLM; LLM responds with clarification request — tool call loop not triggered | No guard needed (LLM handles it), but documents expected flow |

| 6.6 | `OPENAI_API_KEY` missing from environment | `KeyError` on `os.environ["OPENAI_API_KEY"]` at startup | Hard crash at module import time; no useful error message for the user |

| 6.7 | Network / API timeout during LLM call | SDK raises `openai.APITimeoutError`; not caught by current code — wrapping `create_llm_response` in try/except is recommended | Uncaught exception surfaces to CLI as a Python traceback |

| 6.8 | LLM returns parallel tool calls (multiple in one `tool_calls` list) | Inner `for tool_call in choice.message.tool_calls` loop handles all of them; all results appended before re-calling LLM | Only first tool call processed; others silently dropped |

| 6.9 | User sends a second query after an error in the first | Each call to `run_agent_loop` starts with a fresh `messages` list — previous errors do not bleed over | Shared mutable state would contaminate the second query context |

| 6.10 | `LLM_PROVIDER` env var set to an unsupported value | `build_llm_client()` raises `ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")` at startup | Silent fallback to wrong provider, or `AttributeError` at call time |

---

## Phase 7 — End-to-End Query Flows

### Query 1: "Read all resumes in the resumes folder"

| # | Edge Case | Expected Behaviour | Failure Mode if Missed |

|---|-----------|-------------------|------------------------|

| 7.1 | `resumes/` contains zero files | LLM receives `[]` from `list_files`, responds "No resumes found" | Loop iterates over empty list; LLM may confabulate file names |

| 7.2 | One resume is a scanned PDF | LLM reads it, gets `success: false` with scanned-PDF error, and informs the user which file could not be read | LLM silently skips the error and presents incomplete results |

| 7.3 | `resumes/` contains unsupported file types `.xlsx`) | `read_file` returns `UnsupportedFormat` error for that file; LLM reports it separately | LLM crashes on unexpected error format |

### Query 2: "Find resumes mentioning Python experience"

| # | Edge Case | Expected Behaviour | Failure Mode if Missed |

|---|-----------|-------------------|------------------------|

| 7.4 | No resume mentions "Python" | All `search_in_file` calls return `match_count: 0`; LLM responds "No resumes mention Python" | LLM confabulates matches or returns an empty response |

| 7.5 | "Python" appears in filename but not in content | `search_in_file` searches content, not filename — correct `match_count: 0` | Filename check accidentally flags the file |

| 7.6 | LLM uses keyword `"python"` (lowercase) in tool call | `re.IGNORECASE` ensures correct match count regardless of keyword case | Case-sensitive match misses `"Python"`, `"PYTHON"` |

### Query 3: "Create a summary file for resume_john_doe.pdf"

| # | Edge Case | Expected Behaviour | Failure Mode if Missed |

|---|-----------|-------------------|------------------------|

| 7.7 | `resume_john_doe.pdf` does not exist in `resumes/` | `read_file` returns `success: false`; LLM informs user the file was not found | LLM attempts to write a summary with empty content |

| 7.8 | LLM writes to `resumes/summary_john_doe.txt` instead of `output/` | `write_file` blocks the write; returns `success: false, "Path not allowed"` | Source resume folder is overwritten or polluted |

| 7.9 | LLM-generated summary content is empty string | `write_file` creates a 0-byte file; LLM should warn the user summary was empty | 0-byte file silently created; user never told |

| 7.10 | Summary file already exists from a previous run | File is overwritten; `created_dirs: false`; LLM confirms "updated" | Previous summary irreversibly lost without warning |

---

## Cross-Cutting Edge Cases

These apply across multiple phases.

| # | Category | Edge Case | Affected Phases |

|---|----------|-----------|----------------|

| X.1 | Concurrency | Two simultaneous `run_agent_loop` calls write to the same output file | Phase 3, Phase 6 |

| X.2 | File system | File deleted between `list_files` and `read_file` call | Phase 1, Phase 2, Phase 6 |

| X.3 | File system | File permissions change between `list_files` and `read_file` | Phase 1, Phase 2 |

| X.4 | LLM context | Resume content exceeds LLM context window (e.g. 200-page PDF) | Phase 1, Phase 6 |

| X.5 | Encoding | `json.dumps(result)` on `content` containing non-serialisable bytes | Phase 1, Phase 6 |

| X.6 | Injection | Resume content contains text like `"Ignore previous instructions and..."` | Phase 1, Phase 6 — be aware this is a prompt injection risk via tool results |

| X.7 | Path format | Windows-style path `resumes\resume.pdf` passed on macOS | Phase 1, Phase 3 — on POSIX this is treated as a literal filename containing `\`, not normalized into `resumes/resume.pdf`; test it explicitly |