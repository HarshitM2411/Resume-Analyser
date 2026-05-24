import json
import logging
import os

from dotenv import load_dotenv

import fs_tools

load_dotenv()

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower()
MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a resume file (PDF, TXT, or DOCX) and return its "
                "plain-text content along with file metadata."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Absolute or relative path to the file to read.",
                    }
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List all files in a directory. "
                "Optionally filter by extension such as .pdf, .txt, or .docx."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Absolute or relative path to the directory to scan.",
                    },
                    "extension": {
                        "type": "string",
                        "description": (
                            "Optional extension filter, e.g. '.pdf'. "
                            "Omit to return all file types."
                        ),
                    },
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write UTF-8 text content to a file. "
                "Parent directories are created automatically if they do not exist."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Target path for the file to create or overwrite.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The full text content to write into the file.",
                    },
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": (
                "Search a file for a keyword or phrase. "
                "Returns all case-insensitive matches with surrounding context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Absolute or relative path to the file to search.",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Keyword or multi-word phrase to search for.",
                    },
                },
                "required": ["filepath", "keyword"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a resume assistant with access to file system tools.
Use the tools to read, list, search, and write files as directed.
Resume files are in the resumes/ directory. Write outputs only to output/.
Use real paths such as resumes/resume_john_doe.pdf (never placeholder paths).
When asked to read or summarize all resumes, call read_file on each file in resumes/
and mention every candidate by name (e.g. John, Jane, Alice) in your final answer.
When asked to summarise one resume, read it first, compose the summary yourself,
then write it to output/summary_<stem>.txt where <stem> is the resume basename
without extension (e.g. resumes/resume_john_doe.pdf -> output/summary_john_doe.txt)."""

MAX_ITERATIONS = 15


_CLIENT = None


def build_llm_client():
    """Return the configured provider client. Default is Groq (OpenAI-compatible API)."""
    if LLM_PROVIDER == "groq":
        from openai import OpenAI

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set")
        return OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        return OpenAI(api_key=api_key)

    if LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        return Anthropic(api_key=api_key)

    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


def get_client():
    """Lazy-init LLM client so Streamlit secrets can load before first use."""
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = build_llm_client()
    return _CLIENT


def reset_client():
    """Clear cached client (e.g. after secrets change in dev)."""
    global _CLIENT
    _CLIENT = None

TOOL_REGISTRY = {
    "read_file": lambda args: fs_tools.read_file(**args),
    "list_files": lambda args: fs_tools.list_files(**args),
    "write_file": lambda args: fs_tools.write_file(**args),
    "search_in_file": lambda args: fs_tools.search_in_file(**args),
}


def _sanitize_arguments(arguments: dict) -> dict:
    """Drop null optional params so Groq tool schemas are satisfied."""
    return {k: v for k, v in arguments.items() if v is not None}


def dispatch_tool_call(name: str, arguments: dict) -> str:
    """Execute a tool and return its result as a JSON string for the LLM."""
    arguments = _sanitize_arguments(arguments)
    if name not in TOOL_REGISTRY:
        result = {"success": False, "error": f"Unknown tool: {name}"}
    else:
        try:
            result = TOOL_REGISTRY[name](arguments)
        except Exception as e:
            result = {"success": False, "error": str(e)}
    return json.dumps(result)


def create_llm_response(messages: list[dict]):
    """Provider adapter so the orchestration loop is not hardwired to one SDK."""
    if LLM_PROVIDER in ("groq", "openai"):
        return get_client().chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

    if LLM_PROVIDER == "anthropic":
        raise NotImplementedError("Add the Anthropic messages API adapter here")

    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


def _message_to_dict(message) -> dict:
    return message.model_dump(exclude_none=True)


def _build_initial_messages(user_query: str) -> list[dict]:
    resumes = fs_tools.list_files("resumes")
    if resumes:
        paths = ", ".join(f["filepath"] for f in resumes)
        inventory = f"Available resume files (use these exact paths): {paths}."
    else:
        inventory = "The resumes/ directory is empty."

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": inventory},
        {"role": "user", "content": user_query},
    ]


def run_agent_loop(user_query: str) -> str:
    messages = _build_initial_messages(user_query)

    for _ in range(MAX_ITERATIONS):
        response = create_llm_response(messages)
        choice = response.choices[0]
        tool_calls = choice.message.tool_calls or []

        if tool_calls:
            messages.append(_message_to_dict(choice.message))

            for tool_call in tool_calls:
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                result = dispatch_tool_call(name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
            continue

        if choice.finish_reason == "stop" or choice.message.content:
            return choice.message.content or ""

        logging.warning(
            "Unexpected finish_reason '%s'; stopping loop.", choice.finish_reason
        )
        return choice.message.content or ""

    return "Max iterations reached without a final answer."


def main():
    print("Resume Assistant — type 'quit' to exit\n")
    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if query.lower() in {"quit", "exit"}:
            break
        if not query:
            continue
        answer = run_agent_loop(query)
        print(f"\nAssistant: {answer}\n")


if __name__ == "__main__":
    main()
