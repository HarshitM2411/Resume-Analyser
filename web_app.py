"""Basic web UI for manual testing of the resume assistant."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

import fs_tools
from llm_file_assistant import run_agent_loop

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/health")
def health():
    has_key = bool(os.environ.get("GROQ_API_KEY"))
    return jsonify(
        {
            "status": "ok",
            "provider": os.environ.get("LLM_PROVIDER", "groq"),
            "model": os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
            "api_key_configured": has_key,
        }
    )


@app.get("/api/resumes")
def list_resumes():
    return jsonify(fs_tools.list_files("resumes"))


@app.get("/api/output")
def list_output():
    return jsonify(fs_tools.list_files("output"))


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400
    if not os.environ.get("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY is not set in .env"}), 500
    try:
        answer = run_agent_loop(query)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"Resume Assistant UI: http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
