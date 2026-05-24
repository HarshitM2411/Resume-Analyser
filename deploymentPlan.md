# Deployment Plan — Resume Assistant on Streamlit

This document describes how to deploy the **LLM-Powered File System Assistant** on **Streamlit Community Cloud** (or any host that runs `streamlit run`). It assumes the current codebase (`fs_tools.py`, `llm_file_assistant.py`) stays the backend logic; only the **UI layer** changes from Flask (`web_app.py`) to Streamlit.

---

## 1. Deployment target

| Item | Choice |
|------|--------|
| Platform | [Streamlit Community Cloud](https://share.streamlit.io/) (free tier available) |
| Entry point | `streamlit_app.py` (to be added at repo root) |
| LLM | Groq (`GROQ_API_KEY`, OpenAI-compatible SDK) |
| Python | 3.10+ recommended (match local dev, e.g. 3.12) |

**Why Streamlit:** Single Python file for UI, native secrets support, easy sharing via GitHub, no separate static frontend server.

**What stays the same:** `fs_tools.py`, `llm_file_assistant.py`, tool schemas, agent loop, Groq client.

**What is replaced for production UI:** `web_app.py` + `frontend/static/*` (keep locally for reference; Streamlit becomes the deployed UI).

---

## 2. Architecture (deployed)

```text
┌─────────────────────────────────────────────────────────────┐
│  Streamlit Community Cloud                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  streamlit_app.py                                      │  │
│  │  · sidebar: status, file lists, example queries        │  │
│  │  · main: chat history + text input                     │  │
│  │  · file_uploader for resumes (optional)                │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ calls                             │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │  llm_file_assistant.run_agent_loop()                 │  │
│  │  fs_tools (read / list / write / search)             │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ HTTPS                             │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │  Groq API (api.groq.com)                             │  │
│  └───────────────────────────────────────────────────────┘  │
│  Ephemeral disk: /mount/src/.../resumes, output/             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Pre-deployment checklist

### 3.1 Code tasks (before first deploy)

| # | Task | Status |
|---|------|--------|
| 1 | Add `streamlit_app.py` at project root | Done |
| 2 | Add `streamlit>=1.28.0` to `requirements.txt` | Done |
| 3 | Ensure `packages.txt` only if system deps needed (usually not for pdfplumber on Cloud) | Optional |
| 4 | Add `.streamlit/config.toml` (theme, server headless) | Done |
| 5 | Add `.gitignore` entries: `.env`, `output/*`, `__pycache__/` | Done |
| 6 | Do **not** commit `.env` or API keys | Required |
| 7 | Commit sample resumes in `resumes/` OR document upload-only flow | Done (samples in repo + upload UI) |
| 8 | Lazy-import `llm_file_assistant` / catch missing `GROQ_API_KEY` in UI | Done |

### 3.2 Repository layout (target)

```text
airTribe-LLM-Project/
├── streamlit_app.py          # NEW — Cloud entry point
├── fs_tools.py
├── llm_file_assistant.py
├── requirements.txt          # UPDATE — add streamlit
├── .streamlit/
│   └── config.toml           # NEW — theme / server
├── resumes/                  # Sample files (committed) OR empty + upload UI
├── output/                   # Gitignored; created at runtime
├── docs/
├── deploymentPlan.md         # This file
├── web_app.py                # Local dev only (optional)
└── README.md                 # Add deploy URL + setup (recommended)
```

---

## 4. Streamlit app design (map from current UI)

Align with `docs/frontend-design.md` / `frontend-design/DESIGN.md`:

| Current (Flask) | Streamlit equivalent |
|-----------------|----------------------|
| Sidebar connection card | `st.sidebar` + `st.status` / metrics |
| Resume / output lists | `st.sidebar` + `st.dataframe` or custom list |
| Example query chips | `st.button` columns in main area |
| Chat thread | `st.chat_message("user")` / `st.chat_message("assistant")` |
| Composer | `st.chat_input` (preferred) or `st.text_area` + button |
| `/api/chat` | Direct `run_agent_loop(query)` in-process |
| File upload | `st.file_uploader` → save under `resumes/` |

### Minimal `streamlit_app.py` structure (reference)

```python
import streamlit as st
from pathlib import Path
import fs_tools
from llm_file_assistant import run_agent_loop, MODEL, LLM_PROVIDER

st.set_page_config(page_title="Resume Assistant", layout="wide")

# Sidebar: health, list_files("resumes"), list_files("output")
# Main: st.session_state.messages, st.chat_input
# On submit: append user msg, run_agent_loop, append assistant msg, st.rerun
```

Use `st.session_state` for chat history so multi-turn display works without re-calling the LLM for old turns.

---

## 5. Dependencies

### 5.1 `requirements.txt` (deployment)

```text
streamlit>=1.28.0
openai>=1.0.0
pdfplumber
python-docx
python-dotenv
```

**Note:** `flask` is not required on Streamlit Cloud; keep it only if you still run `web_app.py` locally.

### 5.2 Optional pins (stability)

Pin versions after a successful deploy, e.g. `streamlit==1.41.0`, to avoid surprise breakage on Cloud rebuilds.

---

## 6. Secrets and environment variables

### 6.1 Local development

Use `.env` (gitignored):

```env
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
RESUMES_DIR=./resumes
OUTPUT_DIR=./output
```

### 6.2 Streamlit Cloud

In the app settings → **Secrets**, add TOML:

```toml
GROQ_API_KEY = "gsk_..."
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.1-8b-instant"
```

In `streamlit_app.py`, load secrets:

```python
import streamlit as st

def get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        import os
        return os.environ.get(key, default)

# Before importing CLIENT in llm_file_assistant, either:
# - set os.environ from st.secrets at top of streamlit_app.py, or
# - refactor llm_file_assistant to read keys via a small config helper
```

**Important:** `llm_file_assistant.py` currently calls `load_dotenv()` and builds `CLIENT` at import time. For Streamlit, set `os.environ["GROQ_API_KEY"]` from `st.secrets` **before** `import llm_file_assistant`, or refactor to lazy-init `CLIENT` on first query.

### 6.3 Variables reference

| Variable | Required | Purpose |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes | Groq authentication |
| `LLM_PROVIDER` | No | Default `groq` |
| `LLM_MODEL` | No | Default `llama-3.3-70b-versatile` or `llama-3.1-8b-instant` |
| `RESUMES_DIR` | No | Defaults to `./resumes` via `fs_tools` paths |
| `OUTPUT_DIR` | No | Defaults to `./output` |

---

## 7. Streamlit Cloud limitations (must plan for)

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Ephemeral filesystem** | Files written to `output/` are lost on app sleep/redeploy | Treat output as session-only; offer **download** via `st.download_button` for summaries |
| **No persistent disk** | User-uploaded resumes disappear after idle shutdown | Re-upload each session, or commit demo resumes in repo |
| **1 GB RAM (free tier)** | Large PDFs + many agent iterations may OOM | Limit upload size; cap `MAX_ITERATIONS`; use 8B model |
| **Request timeouts** | Long agent loops (60s+) may hit proxy limits | Show spinner; shorten prompts; fewer files per query |
| **Secrets in logs** | Never `st.write(api_key)` | Code review |
| **Public URL** | App is public unless using private Teams plan | Do not embed real PII resumes in public repo |

---

## 8. Deployment steps (Streamlit Community Cloud)

### Step 1 — Prepare Git repository

1. Initialize git if needed: `git init`
2. Ensure `.gitignore` includes `.env`, `output/`, `__pycache__/`
3. Add `streamlit_app.py`, updated `requirements.txt`, `.streamlit/config.toml`
4. Push to **GitHub** (public or private; Cloud supports both with permissions)

### Step 2 — Create Streamlit Cloud app

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Sign in with GitHub
3. **New app** → select repository and branch
4. **Main file path:** `streamlit_app.py`
5. **App URL:** choose subdomain (e.g. `resume-assistant-yourname`)

### Step 3 — Configure secrets

1. App → **Settings** → **Secrets**
2. Paste TOML from section 6.2
3. Save → **Reboot app**

### Step 4 — Advanced settings (optional)

| Setting | Value |
|---------|--------|
| Python version | 3.12 (or match local) |
| Secrets file | Managed in UI (not committed) |

### Step 5 — Verify deploy

1. Open the public URL
2. Sidebar shows **CONNECTED** when `GROQ_API_KEY` is valid
3. Run example: “list the files in the resumes folder”
4. Confirm `read_file` / `search_in_file` on committed sample resumes
5. Run summary query; download generated text if using `st.download_button`

### Step 6 — Monitor

- **Logs:** Cloud dashboard → Manage app → Logs (import errors, Groq 400/429)
- **Usage:** Groq console for token spend per query (see cost notes in project docs)

---

## 9. Local Streamlit run (pre-deploy test)

```bash
cd "c:\Users\ASUS\Desktop\airTribe LLM Project"
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Browser opens at `http://localhost:8501`.

Validate the same three flows as `test_e2e.py`:

1. Read all resumes  
2. Find Python experience  
3. Create summary for `resume_john_doe.pdf`  

---

## 10. Recommended `.streamlit/config.toml`

```toml
[theme]
base = "dark"
primaryColor = "#3b82f6"
backgroundColor = "#0f1419"
secondaryBackgroundColor = "#1a2332"
textColor = "#e7ecf3"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

---

## 11. Security checklist

- [ ] `GROQ_API_KEY` only in Streamlit Secrets or local `.env`
- [ ] `.env` not in git history
- [ ] No resume files with real PII in a **public** repo
- [ ] `write_file` still restricted to `output/` (`fs_tools.is_safe_write_path`)
- [ ] `read_file` restricted to `resumes/` and `output/`
- [ ] Rate-limit or disclaimer if app is public (Groq quota abuse)

---

## 12. Cost and quotas (operational)

| Resource | Notes |
|----------|--------|
| Streamlit Cloud | Free tier: 1 private app or public apps with limits; see [Streamlit pricing](https://streamlit.io/cloud) |
| Groq API | Pay-per-token; ~$0.0001–0.0003 per simple query on `llama-3.1-8b-instant` |
| Groq free tier | RPM/TPM limits; heavy traffic may return 429 |

Use `llama-3.1-8b-instant` for demos; use `llama-3.3-70b-versatile` only when quality justifies ~12× cost.

---

## 13. CI / quality gate (optional)

Before each deploy:

```bash
pip install -r requirements.txt
python -c "import fs_tools, llm_file_assistant; print('imports ok')"
# After streamlit_app.py exists:
streamlit run streamlit_app.py --server.headless true &
# manual smoke test
python test_e2e.py   # CLI/agent test (uses Groq API)
```

---

## 14. Rollback and alternatives

| Scenario | Action |
|----------|--------|
| Streamlit deploy fails | Check Cloud logs; fix `requirements.txt` / import order |
| Groq errors | Verify secrets, model name, tool-call schema issues |
| Revert UI | Keep using local `python web_app.py` (Flask) |
| Need persistence | Move to VPS + Docker, or add S3 for resumes/output |
| Need custom domain | Streamlit Teams or reverse proxy on own server |

---

## 15. Implementation order (recommended)

1. **Refactor** `llm_file_assistant` for lazy `CLIENT` init (secrets-friendly)  
2. **Create** `streamlit_app.py` with chat + sidebar  
3. **Update** `requirements.txt`  
4. **Test** locally with `streamlit run`  
5. **Push** to GitHub  
6. **Deploy** on Streamlit Cloud + configure secrets  
7. **Document** public URL in `README.md`  
8. (Optional) Deprecate Flask UI for production or keep for dev only  

---

## 16. Post-deployment acceptance criteria

| # | Criterion |
|---|-----------|
| 1 | App loads without import errors |
| 2 | Missing `GROQ_API_KEY` shows clear UI error, not stack trace |
| 3 | Example queries return answers within timeout |
| 4 | Resume list reflects `resumes/` (committed or uploaded) |
| 5 | Summary flow produces downloadable or visible output |
| 6 | No API keys visible in browser or logs |

---

## 17. Quick reference links

- [Streamlit deploy docs](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)
- [Streamlit secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Groq console](https://console.groq.com/)
- [Groq pricing](https://groq.com/pricing)
- Project design: `docs/frontend-design.md`, `frontend-design/DESIGN.md`

---

*Version: 1.0 — Streamlit deployment plan for Resume Assistant (Groq + fs_tools + llm_file_assistant).*
