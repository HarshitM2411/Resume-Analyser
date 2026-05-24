"""Rough token/cost estimate for one user query (no API spend for full agent loop)."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

import fs_tools
from llm_file_assistant import (
    MODEL,
    SYSTEM_PROMPT,
    TOOL_SCHEMAS,
    _build_initial_messages,
    create_llm_response,
)

# ~4 chars per token (rough; good enough for cost ballpark)
def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def message_list_tokens(messages: list) -> int:
    total = 0
    for m in messages:
        content = m.get("content") or ""
        if isinstance(content, str):
            total += est_tokens(content)
        tool_calls = m.get("tool_calls")
        if tool_calls:
            total += est_tokens(json.dumps(tool_calls))
    return total


def cost_usd(input_tokens: int, output_tokens: int, model: str) -> float:
    pricing = {
        "llama-3.3-70b-versatile": (0.59, 0.79),
        "llama-3.1-8b-instant": (0.05, 0.08),
    }
    pin, pout = pricing.get(model, (0.59, 0.79))
    return (input_tokens / 1_000_000) * pin + (output_tokens / 1_000_000) * pout


schemas_tokens = est_tokens(json.dumps(TOOL_SCHEMAS))

print("=" * 60)
print(f"Model from .env: {MODEL}")
print(f"TOOL_SCHEMAS (sent every API call): ~{schemas_tokens:,} tokens")
print(f"SYSTEM_PROMPT: ~{est_tokens(SYSTEM_PROMPT):,} tokens")
print()

resumes = fs_tools.list_files("resumes")
read_sizes = []
for f in resumes:
    r = fs_tools.read_file(f["filepath"])
    if r.get("success"):
        t = est_tokens(r["content"])
        read_sizes.append((f["filename"], t))

print("Resume content sizes (if read_file returns full text):")
for name, t in read_sizes:
    print(f"  {name}: ~{t:,} tokens")
print()

scenarios = [
    {
        "name": "Simple — list files only",
        "rounds": 2,
        "extra_tool_tokens": 400,
        "output_per_round": [80, 200],
    },
    {
        "name": "Medium — search 3 resumes",
        "rounds": 4,
        "extra_tool_tokens": 2500,
        "output_per_round": [100, 80, 80, 350],
    },
    {
        "name": "Heavy — read all resumes (3 files)",
        "rounds": 5,
        "extra_tool_tokens": sum(t for _, t in read_sizes) + 800,
        "output_per_round": [100, 80, 80, 80, 500],
    },
    {
        "name": "Heavy — summarize one PDF + write",
        "rounds": 4,
        "extra_tool_tokens": (read_sizes[0][1] if read_sizes else 800) + 600,
        "output_per_round": [100, 80, 80, 400],
    },
]

for q in ["list the files in the resumes folder"]:
    init = _build_initial_messages(q)
    init_tokens = message_list_tokens(init)
    print(f"Initial messages (2 system + user): ~{init_tokens:,} tokens")
    print()

print("SCENARIO ESTIMATES (per user query)")
print("-" * 60)
for s in scenarios:
    cumulative_context = init_tokens
    total_input = 0
    total_output = sum(s["output_per_round"])

    for i, out_tok in enumerate(s["output_per_round"], start=1):
        # Each call: full history + tools schemas + new content
        call_input = schemas_tokens + cumulative_context + s["extra_tool_tokens"] // s["rounds"]
        total_input += call_input
        cumulative_context += out_tok + s["extra_tool_tokens"] // s["rounds"] + 150

    c70 = cost_usd(total_input, total_output, "llama-3.3-70b-versatile")
    c8 = cost_usd(total_input, total_output, "llama-3.1-8b-instant")
    print(f"{s['name']}")
    print(f"  ~{s['rounds']} LLM API calls")
    print(f"  Est. input tokens (total):  ~{total_input:,}")
    print(f"  Est. output tokens (total): ~{total_output:,}")
    print(f"  Cost @ llama-3.3-70b:  ${c70:.4f}")
    print(f"  Cost @ llama-3.1-8b:   ${c8:.4f}")
    print()

# Optional: one real cheap call for usage metadata
if os.environ.get("GROQ_API_KEY") and "--live" in sys.argv:
    print("LIVE single completion (list files query, may still do tools)...")
    from llm_file_assistant import run_agent_loop

    resp = create_llm_response(_build_initial_messages("list the files in the resumes folder"))
    u = getattr(resp, "usage", None)
    if u:
        print(f"  usage: prompt={u.prompt_tokens} completion={u.completion_tokens} total={u.total_tokens}")
        print(f"  cost this call only: ${cost_usd(u.prompt_tokens, u.completion_tokens, MODEL):.6f}")
