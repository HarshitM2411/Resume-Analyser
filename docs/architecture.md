# Architecture: LLM-Powered File System Assistant

---

## 1. High-Level System Overview

```mermaid

graph TB

    User["👤 User<br/>(Natural Language Query)"]

    Assistant["llm_file_[assistant.py](http://assistant.py)<br/>LLM Orchestration Layer"]

    LLM["LLM Provider<br/>(Groq — OpenAI-compatible API)"]

    Tools["fs_[tools.py](http://tools.py)<br/>File System Tools"]

    FS["Local File System<br/>(resumes/ · output/)"]

    User -->|"query string"| Assistant

    Assistant -->|"messages + tool schemas"| LLM

    LLM -->|"tool_call requests"| Assistant

    Assistant -->|"dispatches call"| Tools

    Tools -->|"read / write / search"| FS

    FS -->|"raw file data"| Tools

    Tools -->|"structured dict result"| Assistant

    Assistant -->|"tool_result message"| LLM

    LLM -->|"final natural language answer"| Assistant

    Assistant -->|"response"| User

```

---

## 2. Module Decomposition

```mermaid

graph LR

    subgraph "Part B — llm_file_[assistant.py](http://assistant.py)"

        CLI["CLI / REPL<br/>chat interface"]

        Orchestrator["Orchestrator<br/>run_agent_loop()"]

        Dispatcher["Tool Dispatcher<br/>dispatch_tool_call()"]

        Schemas["Tool Schema Registry<br/>TOOL_SCHEMAS list"]

        Summarizer["Summary Composer<br/>LLM-generated summary text"]

        Config["Config Loader<br/>.env + settings"]

    end

    subgraph "Part A — fs_[tools.py](http://tools.py)"

        RF["read_file()"]

        LF["list_files()"]

        WF["write_file()"]

        SF["search_in_file()"]

    end

    subgraph "LLM Provider"

        GRQ["Groq<br/>llama-3.3-70b-versatile<br/>(default)"]

    end

    subgraph "File System"

        RES["resumes/"]

        OUT["output/"]

    end

    CLI --> Orchestrator

    Orchestrator --> Schemas

    Orchestrator --> GRQ

    Orchestrator --> Dispatcher

    Orchestrator --> Summarizer

    Config --> Orchestrator

    Dispatcher --> RF

    Dispatcher --> LF

    Dispatcher --> WF

    Dispatcher --> SF

    RF --> RES

    LF --> RES

    LF --> OUT

    WF --> OUT

    SF --> RF

```

---

## 3. Agentic Tool-Calling Loop (Sequence Diagram)

```mermaid

sequenceDiagram

    actor User

    participant A as Orchestrator<br/>(llm_file_[assistant.py](http://assistant.py))

    participant L as LLM API

    participant D as Dispatcher

    participant T as fs_[tools.py](http://tools.py)

    participant FS as File System

    User->>A: "Find resumes mentioning Python"

    A->>L: messages=[{role:user, content:query}]<br/>tools=[TOOL_SCHEMAS]

    L-->>A: tool_call: list_files({directory:"resumes"})

    A->>D: dispatch("list_files", {directory:"resumes"})

    D->>T: list_files("resumes")

    T->>FS: os.scandir("resumes/")

    FS-->>T: file entries

    T-->>D: [{filename, filepath, ...}, ...]

    D-->>A: tool result dict

    A->>L: messages += tool_result

    L-->>A: tool_call: search_in_file({filepath:"resume_john_doe.pdf", keyword:"Python"})

    A->>D: dispatch("search_in_file", {...})

    D->>T: search_in_file(filepath, "Python")

    T->>T: read_file(filepath)  [internal]

    T->>FS: open / pdfplumber / docx

    FS-->>T: raw bytes

    T-->>T: extracted text

    T->>T: re.finditer(pattern, text, IGNORECASE)

    T-->>D: {match_count:3, matches:[...]}

    D-->>A: tool result dict

    Note over A,L: Loop repeats for each resume file

    A->>L: messages += all tool_results

    L-->>A: Final answer (natural language)

    A-->>User: "3 resumes mention Python: john_doe, jane_smith, alice_wang..."

```

### Summary File Creation Flow

```mermaid

sequenceDiagram

    actor User

    participant A as Orchestrator<br/>(llm_file_[assistant.py](http://assistant.py))

    participant L as LLM API

    participant D as Dispatcher

    participant T as fs_[tools.py](http://tools.py)

    participant FS as File System

    User->>A: "Create a summary file for resume_john_doe.pdf"

    A->>L: messages + TOOL_SCHEMAS

    L-->>A: tool_call: read_file({filepath:"resumes/resume_john_doe.pdf"})

    A->>D: dispatch("read_file", {...})

    D->>T: read_file("resumes/resume_john_doe.pdf")

    T->>FS: extract text from file

    FS-->>T: raw file contents

    T-->>D: {success:true, content:"...", metadata:{...}}

    D-->>A: tool result

    A->>L: messages += tool_result

    Note over L: LLM composes summary text from extracted resume content

    L-->>A: tool_call: write_file({filepath:"output/summary_john_doe.txt", content:"summary text"})

    A->>D: dispatch("write_file", {...})

    D->>T: write_file("output/summary_john_doe.txt", "summary text")

    T->>FS: write UTF-8 file

    FS-->>T: write success

    T-->>D: {success:true, bytes_written:...}

    D-->>A: tool result

    A->>L: messages += tool_result

    L-->>A: Final confirmation response

    A-->>User: "Summary file created successfully."

```

---

## 4. `fs_tools.py` — Internal Tool Architecture

```mermaid

graph TD

    subgraph "read_file(filepath)"

        RF_IN["filepath: str"]

        RF_EXT["detect extension<br/>.pdf / .txt / .docx"]

        RF_TXT["open() UTF-8<br/>read text"]

        RF_PDF["pdfplumber<br/>extract_text() per page"]

        RF_DOC["python-docx<br/>paragraph.text join"]

        RF_NORM["normalize_text()<br/>strip whitespace"]

        RF_META["build metadata<br/>size · word_count · modified_at"]

        RF_OUT["return dict<br/>{success, content, metadata}"]

        RF_ERR["catch Exception<br/>return {success:false, error}"]

        RF_IN --> RF_EXT

        RF_EXT -->|".txt"| RF_TXT

        RF_EXT -->|".pdf"| RF_PDF

        RF_EXT -->|".docx"| RF_DOC

        RF_TXT --> RF_NORM

        RF_PDF --> RF_NORM

        RF_DOC --> RF_NORM

        RF_NORM --> RF_META

        RF_META --> RF_OUT

        RF_EXT -->|"unsupported"| RF_ERR

        RF_PDF -->|"exception"| RF_ERR

    end

    subgraph "list_files(directory, extension)"

        LF_IN["directory · extension"]

        LF_CHK["os.path.isdir() check"]

        LF_SCAN["os.scandir()"]

        LF_FILT["filter by extension<br/>(case-insensitive)"]

        LF_SORT["sort by filename"]

        LF_META2["stat() → size · modified_at"]

        LF_OUT["return list[dict]"]

        LF_IN --> LF_CHK

        LF_CHK -->|"exists"| LF_SCAN

        LF_CHK -->|"missing"| LF_OUT

        LF_SCAN --> LF_FILT

        LF_FILT --> LF_SORT

        LF_SORT --> LF_META2

        LF_META2 --> LF_OUT

    end

    subgraph "write_file(filepath, content)"

        WF_IN["filepath · content"]

        WF_SEC["security check<br/>path within allowed dirs"]

        WF_DIRS["os.makedirs(exist_ok=True)"]

        WF_WRITE["open(w, utf-8).write()"]

        WF_OUT["return {success, bytes_written, created_dirs}"]

        WF_ERR2["catch PermissionError / OSError<br/>return {success:false, error}"]

        WF_IN --> WF_SEC

        WF_SEC -->|"safe"| WF_DIRS

        WF_SEC -->|"unsafe"| WF_ERR2

        WF_DIRS --> WF_WRITE

        WF_WRITE --> WF_OUT

        WF_WRITE -->|"exception"| WF_ERR2

    end

    subgraph "search_in_file(filepath, keyword)"

        SF_IN["filepath · keyword"]

        SF_READ["calls read_file(filepath)"]

        SF_CHK2["check read success"]

        SF_RE["re.finditer(keyword, text, IGNORECASE)"]

        SF_CTX["extract context window<br/>(±100 chars per match)"]

        SF_OUT["return {match_count, matches[]}"]

        SF_ERR3["propagate read error"]

        SF_IN --> SF_READ

        SF_READ -->|"success:true"| SF_CHK2

        SF_READ -->|"success:false"| SF_ERR3

        SF_CHK2 --> SF_RE

        SF_RE --> SF_CTX

        SF_CTX --> SF_OUT

    end

```

---

## 5. `llm_file_assistant.py` — Orchestrator State Machine

```mermaid

stateDiagram-v2

    [*] --> Idle

    Idle --> BuildingRequest : user sends query

    BuildingRequest --> CallingLLM : append user message\nattach tool schemas

    CallingLLM --> EvaluatingResponse : LLM responds

    EvaluatingResponse --> ExecutingTools : response.finish_reason\n== "tool_calls"

    EvaluatingResponse --> RespondingToUser : response.finish_reason\n== "stop"

    ExecutingTools --> CollectingResults : dispatch each tool_call\nto fs_[tools.py](http://tools.py)

    CollectingResults --> CallingLLM : append tool_results\nto message history

    RespondingToUser --> Idle : print final answer\nto user

    ExecutingTools --> HandlingToolError : tool returns success:false

    HandlingToolError --> CallingLLM : append error as tool_result\nLLM decides next step

```

---

## 6. Data Flow: Message History Structure

Each turn appends to a running `messages` list passed to the LLM:

```

messages = [

  {role: "system",    content: SYSTEM_PROMPT},

    {role: "user",      content: "Create a summary file for resume_john_doe.pdf"},

    {role: "assistant", tool_calls: [{id, name:"read_file", arguments:{...}}]},

    {role: "tool",      tool_call_id: id, content: "{content:'...', metadata:{...}}"},

    {role: "assistant", tool_calls: [{id, name:"write_file", arguments:{...}}]},

    {role: "tool",      tool_call_id: id, content: "{success:true, bytes_written:...}"},

  ...

  {role: "assistant", content: "Final natural language answer"}

]

```

```mermaid

graph LR

    M0["system\nprompt"] --> M1["user\nquery"]

    M1 --> M2["assistant\ntool_calls"]

    M2 --> M3["tool\nresult"]

    M3 --> M4["assistant\nsummary draft\nand tool_calls"]

    M4 --> M5["tool\nwrite result"]

    M5 --> M6["assistant\nfinal answer"]

    style M0 fill:#e8f4fd,stroke:#2980b9

    style M1 fill:#eafaf1,stroke:#27ae60

    style M2 fill:#fef9e7,stroke:#f39c12

    style M3 fill:#fdedec,stroke:#e74c3c

    style M4 fill:#fef9e7,stroke:#f39c12

    style M5 fill:#fdedec,stroke:#e74c3c

    style M6 fill:#eafaf1,stroke:#27ae60

```

---

## 7. Security Architecture

```mermaid

graph TD

    subgraph "Threat: Path Traversal"

        PT_IN["filepath input<br/>e.g. '../../etc/passwd'"]

        PT_RESOLVE["os.path.realpath(filepath)"]

        PT_CHECK["startswith(ALLOWED_ROOT)?"]

        PT_BLOCK["return {success:false,<br/>error:'Path not allowed'}"]

        PT_ALLOW["proceed with I/O"]

        PT_IN --> PT_RESOLVE

        PT_RESOLVE --> PT_CHECK

        PT_CHECK -->|"No"| PT_BLOCK

        PT_CHECK -->|"Yes"| PT_ALLOW

    end

    subgraph "Threat: Credential Exposure"

        ENV[".env file"]

        DOTENV["python-dotenv\nload_dotenv()"]

        OS_ENV["os.environ.get('GROQ_API_KEY')"]

        CLIENT["LLM client init"]

        ENV --> DOTENV

        DOTENV --> OS_ENV

        OS_ENV --> CLIENT

    end

    subgraph "Threat: Unconstrained Write"

        WR_PATH["write target path"]

        WR_ROOT["resolve against OUTPUT_DIR"]

        WR_GATE["within output/ ?"]

        WR_DENY["reject write"]

        WR_OK["write file"]

        WR_PATH --> WR_ROOT

        WR_ROOT --> WR_GATE

        WR_GATE -->|"No"| WR_DENY

        WR_GATE -->|"Yes"| WR_OK

    end

```

---

## 8. File Format Handling Decision Tree

```mermaid

graph TD

    FP["filepath received"]

    EXT["extract extension<br/>Path(filepath).suffix.lower()"]

    EXT -->|".txt"| TXT["open(filepath, r, encoding=utf-8)\[n.read](http://n.read)()"]

    EXT -->|".pdf"| PDF["[pdfplumber.open](http://pdfplumber.open)(filepath)\npages → extract_text()"]

    EXT -->|".docx"| DOCX["docx.Document(filepath)\nparagraphs → .text join"]

    EXT -->|"other"| UNS["UnsupportedFormatError\nreturn success:false"]

    TXT --> NORM["normalize_text()"]

    PDF --> SCANCHK{"any text\nextracted?"}

    SCANCHK -->|"Yes"| NORM

    SCANCHK -->|"No (scanned PDF)"| SCAN_ERR["return success:false\nerror: 'Scanned PDF — no extractable text'"]

    DOCX --> NORM

    NORM --> META["build metadata dict"]

    META --> RESP["return success:true response"]

```

---

## 9. Directory & File Layout

```

airTribe LLM Project/

│

├── docs/

│   ├── [context.md](http://context.md)          ← problem statement & specs

│   └── [architecture.md](http://architecture.md)     ← this file

│

├── resumes/                ← INPUT (read-only at runtime)

│   ├── resume_john_doe.pdf

│   ├── resume_jane_smith.docx

│   └── resume_alice_wang.txt

│

├── output/                 ← OUTPUT (write_file target)

│   └── summary_john_doe.txt

│

├── fs_[tools.py](http://tools.py)             ← Part A: 4 tool functions

├── llm_file_[assistant.py](http://assistant.py)   ← Part B: LLM orchestration + CLI

├── requirements.txt

└── .env                    ← secrets (gitignored)

```

---

## 10. Component Responsibility Summary

| Component | File | Responsibility |

|-----------|------|---------------|

| Tool functions | `fs_tools.py` | All file I/O; return structured dicts; no exceptions to caller |

| Tool schemas | `llm_file_assistant.py` | JSON Schema definitions for LLM function calling |

| Orchestrator | `llm_file_assistant.py` | Message history management; agentic loop; LLM API calls |

| Summary composer | `llm_file_assistant.py` | Converts extracted resume text into a grounded summary before `write_file()` |

| Dispatcher | `llm_file_assistant.py` | Routes `tool_call` names → Python functions |

| Config | `.env` + `python-dotenv` | Provider selection, API keys, directory paths |

| Security guard | `fs_tools.py` | Path traversal checks on every read/write call |