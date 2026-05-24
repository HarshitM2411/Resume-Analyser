"""Streamlit UI for Resume Assistant — deploy entry point for Streamlit Cloud."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
RESUMES_DIR = PROJECT_ROOT / "resumes"
OUTPUT_DIR = PROJECT_ROOT / "output"

EXAMPLE_QUERIES = [
    ("Read all resumes", "Read all resumes in the resumes folder"),
    ("Find Python experience", "Find resumes mentioning Python experience"),
    ("Summarize John Doe PDF", "Create a summary file for resume_john_doe.pdf"),
    ("List resume files", "list the files in the resumes folder"),
]

ALLOWED_UPLOAD_EXT = {".pdf", ".docx", ".txt"}


def _apply_streamlit_secrets() -> None:
    """Map Streamlit Cloud secrets into os.environ before LLM client init."""
    try:
        secrets = st.secrets
        for key in ("GROQ_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "OPENAI_API_KEY"):
            if key in secrets:
                os.environ[key] = str(secrets[key])
    except Exception:
        pass

    from dotenv import load_dotenv

    load_dotenv()


def _ensure_dirs() -> None:
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{round(size / 1024)} KB"
    return f"{(size / (1024 * 1024)):.1f} MB"


def _ext_badge(ext: str) -> str:
    e = (ext or "").lower().lstrip(".")
    return e.upper() if e else "FILE"


def _api_key_configured() -> bool:
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        return bool(os.environ.get("GROQ_API_KEY"))
    if provider == "openai":
        return bool(os.environ.get("OPENAI_API_KEY"))
    return False


def _render_connection_card() -> None:
    st.markdown("##### Connection")
    provider = os.environ.get("LLM_PROVIDER", "groq")
    model = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
    if _api_key_configured():
        st.success(f"Connected · {provider}")
        st.caption(f"Model: `{model}`")
    else:
        st.error("GROQ_API_KEY not configured")
        st.caption("Add secrets in Streamlit Cloud or a local `.env` file.")


def _render_file_list(files: list, *, compact: bool = False) -> None:
    if not files:
        st.caption("No files")
        return
    for f in files:
        badge = _ext_badge(f.get("extension", ""))
        label = f"{f['filename']} · {_format_bytes(f['size_bytes'])} · {badge}"
        if compact:
            st.text(label)
        else:
            st.markdown(f"**{f['filename']}**  \n`{_format_bytes(f['size_bytes'])}` · {badge}")


def _save_upload(uploaded_file) -> None:
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXT:
        st.sidebar.warning(f"Skipped {uploaded_file.name}: unsupported type")
        return
    dest = RESUMES_DIR / Path(uploaded_file.name).name
    dest.write_bytes(uploaded_file.getvalue())
    st.sidebar.success(f"Uploaded {dest.name}")


def _init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def main() -> None:
    _apply_streamlit_secrets()
    _ensure_dirs()

    import fs_tools
    from llm_file_assistant import run_agent_loop

    st.set_page_config(
        page_title="Resume Assistant",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_session_state()

    # ── Sidebar ──────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("Resume Assistant")
        st.caption("Local AI resume Q&A · Groq")
        _render_connection_card()
        st.divider()

        uploaded = st.file_uploader(
            "Upload resume",
            type=["pdf", "docx", "txt"],
            help="Files are saved to resumes/ for this session.",
        )
        if uploaded is not None:
            if st.button("Save upload", use_container_width=True):
                _save_upload(uploaded)
                st.rerun()

        if st.button("Refresh files", use_container_width=True):
            st.rerun()

        st.markdown("**RESUMES**")
        resumes = fs_tools.list_files("resumes")
        _render_file_list(resumes)

        st.markdown("**OUTPUT**")
        outputs = fs_tools.list_files("output")
        _render_file_list(outputs, compact=True)

        for out in outputs:
            path = PROJECT_ROOT / out["filepath"]
            if path.is_file():
                with open(path, encoding="utf-8", errors="replace") as f:
                    st.download_button(
                        label=f"Download {out['filename']}",
                        data=f.read(),
                        file_name=out["filename"],
                        key=f"dl_{out['filename']}",
                        use_container_width=True,
                    )

        if st.button("New analysis", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.rerun()

    # ── Main workspace ───────────────────────────────────────────────────
    col_title, col_badge = st.columns([4, 1])
    with col_title:
        st.header("AI Resume Workspace")
        st.caption("Ask questions across local PDF, DOCX, and TXT resumes.")
    with col_badge:
        st.caption(f"Streamlit · {os.environ.get('LLM_PROVIDER', 'groq')}")

    st.markdown("**Quick actions**")
    chip_cols = st.columns(len(EXAMPLE_QUERIES))
    for col, (label, query) in zip(chip_cols, EXAMPLE_QUERIES):
        with col:
            if st.button(label, use_container_width=True, disabled=not _api_key_configured()):
                st.session_state.pending_query = query

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pending = st.session_state.pop("pending_query", None)
    prompt = st.chat_input(
        "Ask about skills, experience, or create a summary…",
        disabled=not _api_key_configured(),
    )
    user_text = pending or prompt

    if user_text:
        if not _api_key_configured():
            st.error("Set GROQ_API_KEY in secrets or .env before chatting.")
            return

        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    answer = run_agent_loop(user_text)
                except Exception as e:
                    answer = f"**Error:** {e}"
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})


main()
