# Resume Analyser

LLM-powered assistant that reads, searches, and summarizes resume files (PDF, DOCX, TXT) using Groq and local file-system tools.

## Run locally (Streamlit — recommended for deploy)

```bash
pip install -r requirements.txt
```

Set `GROQ_API_KEY` in `.env` or `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`).

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501

## Run locally (Flask UI — dev)

```bash
python web_app.py
```

Open http://127.0.0.1:5000

## Deploy on Streamlit Cloud

1. Push this repo to GitHub (do not commit `.env`).
2. Go to [share.streamlit.io](https://share.streamlit.io/) → **New app**.
3. **Main file path:** `streamlit_app.py`
4. **Secrets** (TOML):

```toml
GROQ_API_KEY = "gsk_..."
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.1-8b-instant"
```

5. Deploy and open the public URL.

See [deploymentPlan.md](deploymentPlan.md) for full details, limits, and security notes.

## Environment variables

| Variable | Required | Default |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes (Groq) | — |
| `LLM_PROVIDER` | No | `groq` |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` |

## Project layout

| Path | Purpose |
|------|---------|
| `streamlit_app.py` | Streamlit entry (Cloud deploy) |
| `llm_file_assistant.py` | Agent loop + Groq client |
| `fs_tools.py` | File tools (read, list, write, search) |
| `resumes/` | Input resumes |
| `output/` | Generated summaries (ephemeral on Cloud) |

## Tests

```bash
python test_e2e.py
```

Requires `GROQ_API_KEY` in `.env`.
