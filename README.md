# Resume Analyser

An LLM-powered resume assistant that can read, search, compare, and summarize local resume files. It supports PDF, DOCX, and TXT files, uses a tool-calling agent loop, and writes generated summaries to a controlled output folder.

## Features

- Chat with resumes through the Streamlit UI, Flask dev UI, or CLI.
- Upload and inspect resumes from `resumes/`.
- Read PDF, DOCX, and TXT files with metadata extraction.
- Search resume text with case-insensitive context snippets.
- Generate summary files under `output/`.
- Restrict reads to `resumes/` and `output/`, and writes to `output/`.

## Tech Stack

- Python
- Streamlit for the deployable UI
- Flask for the local development UI
- Groq via the OpenAI-compatible SDK
- `pdfplumber` for PDFs
- `python-docx` for DOCX files
- `python-dotenv` for local configuration

## Setup

```bash
pip install -r requirements.txt
```

Create a local `.env` file:

```env
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
```

For Streamlit secrets, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` locally or paste the same keys into Streamlit Cloud secrets.

## Run

Streamlit is the recommended app entry point:

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

Flask UI is available for local development:

```bash
python web_app.py
```

Open `http://127.0.0.1:5000`.

CLI mode is also available:

```bash
python llm_file_assistant.py
```

## Usage

Place resumes in `resumes/` or upload them from the Streamlit sidebar. Example prompts:

- `Read all resumes in the resumes folder`
- `Find resumes mentioning Python experience`
- `Create a summary file for resume_alice_wang.txt`
- `List the files in the resumes folder`

Generated files are saved in `output/`.

## Configuration

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | Yes for Groq | - | Primary API key |
| `LLM_PROVIDER` | No | `groq` | `groq` or `openai` |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` | Model used by the agent |
| `OPENAI_API_KEY` | Yes for OpenAI | - | Only needed when `LLM_PROVIDER=openai` |

## Project Layout

| Path | Purpose |
| --- | --- |
| `streamlit_app.py` | Streamlit UI and Cloud entry point |
| `web_app.py` | Flask development UI |
| `llm_file_assistant.py` | LLM client, tool schemas, and agent loop |
| `fs_tools.py` | File read, list, write, and search tools |
| `resumes/` | Resume input files |
| `output/` | Generated summaries and outputs |
| `docs/` | Architecture, evaluation, and implementation notes |
| `scripts/` | Utility scripts |
| `test_e2e.py` | End-to-end validation script |

## How It Works

The UI sends a natural-language query to `run_agent_loop()`. The LLM chooses from four file tools: `read_file`, `list_files`, `write_file`, and `search_in_file`. Tool results are returned to the model until it can produce a final answer or create an output file.

File access is intentionally scoped: resumes are read from `resumes/`, generated content is written to `output/`, and path traversal attempts are rejected.

## Deploy

1. Push the repo to GitHub without committing `.env` or real secrets.
2. Create a new app on [Streamlit Community Cloud](https://share.streamlit.io/).
3. Set the main file path to `streamlit_app.py`.
4. Add secrets:

```toml
GROQ_API_KEY = "gsk_..."
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.3-70b-versatile"
```

See `deploymentPlan.md` for deployment details, limits, and security notes.

## Test

```bash
python test_e2e.py
```

The e2e test requires a valid `GROQ_API_KEY` and sample resumes in `resumes/`.
