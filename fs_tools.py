import logging
import os
import re
from datetime import datetime
from pathlib import Path

# ── security helpers ────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent
RESUMES_DIR = (PROJECT_ROOT / "resumes").resolve()
OUTPUT_DIR = (PROJECT_ROOT / "output").resolve()


def is_relative_to(path: Path, root: Path) -> bool:
    """Python 3.8+ compatible check for whether path is inside root."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_safe_read_path(filepath: str) -> bool:
    """Allow reads only from the resumes and output directories."""
    resolved = Path(filepath).expanduser().resolve(strict=False)
    return is_relative_to(resolved, RESUMES_DIR) or is_relative_to(resolved, OUTPUT_DIR)


def is_safe_write_path(filepath: str) -> bool:
    """Allow writes only inside the output directory."""
    resolved = Path(filepath).expanduser().resolve(strict=False)
    return is_relative_to(resolved, OUTPUT_DIR)


def normalize_text(text: str) -> str:
    """Collapse runs of whitespace; strip leading/trailing blanks."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def read_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def read_pdf(filepath: str) -> str:
    import pdfplumber

    pages_text = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
    if not pages_text:
        raise ValueError("Scanned PDF — no extractable text layer found")
    return "\n".join(pages_text)


def read_docx(filepath: str) -> str:
    from docx import Document

    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def read_file(filepath: str) -> dict:
    try:
        if not is_safe_read_path(filepath):
            return {
                "success": False,
                "filepath": filepath,
                "error": "Path not allowed — outside permitted directories",
            }

        path = Path(filepath)
        if not path.exists():
            return {
                "success": False,
                "filepath": filepath,
                "error": f"FileNotFoundError: {filepath} does not exist",
            }

        ext = path.suffix.lower()
        dispatch = {".txt": read_txt, ".pdf": read_pdf, ".docx": read_docx}
        if ext not in dispatch:
            return {
                "success": False,
                "filepath": filepath,
                "error": f"UnsupportedFormat: '{ext}' is not supported",
            }

        raw_text = dispatch[ext](filepath)
        content = normalize_text(raw_text)
        stat = path.stat()
        metadata = {
            "filename": path.name,
            "size_bytes": stat.st_size,
            "word_count": len(content.split()),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(
                timespec="seconds"
            ),
        }

        if ext == ".pdf":
            import pdfplumber

            with pdfplumber.open(filepath) as pdf:
                metadata["page_count"] = len(pdf.pages)

        return {
            "success": True,
            "filepath": filepath,
            "format": ext.lstrip("."),
            "content": content,
            "metadata": metadata,
        }

    except Exception as e:
        return {"success": False, "filepath": filepath, "error": str(e)}


def list_files(directory: str, extension: str = None) -> list:
    try:
        if not os.path.isdir(directory):
            logging.warning("list_files: directory '%s' does not exist", directory)
            return []

        entries = []
        with os.scandir(directory) as it:
            for entry in it:
                if not entry.is_file():
                    continue

                entry_ext = Path(entry.name).suffix.lower()

                if extension is not None:
                    wanted = extension if extension.startswith(".") else f".{extension}"
                    if entry_ext != wanted.lower():
                        continue

                stat = entry.stat()
                entries.append(
                    {
                        "filename": entry.name,
                        "filepath": os.path.join(directory, entry.name),
                        "extension": entry_ext,
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(
                            timespec="seconds"
                        ),
                    }
                )

        return sorted(entries, key=lambda e: e["filename"].lower())

    except Exception as e:
        logging.error("list_files error: %s", e)
        return []


def write_file(filepath: str, content: str) -> dict:
    try:
        # Security gate — only allow writes inside output/
        if not is_safe_write_path(filepath):
            return {
                "success": False,
                "filepath": filepath,
                "error": "Path not allowed — writes are restricted to the output directory",
            }

        path = Path(filepath)
        dir_existed = path.parent.exists()
        os.makedirs(path.parent, exist_ok=True)

        encoded = content.encode("utf-8")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "filepath": filepath,
            "bytes_written": len(encoded),
            "created_dirs": not dir_existed,
        }

    except Exception as e:
        return {"success": False, "filepath": filepath, "error": str(e)}


def extract_context(text: str, match, window: int = 100) -> str:
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def search_in_file(filepath: str, keyword: str) -> dict:
    read_result = read_file(filepath)
    if not read_result["success"]:
        return {
            "success": False,
            "filepath": filepath,
            "keyword": keyword,
            "error": read_result["error"],
        }

    text = read_result["content"]
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    matches_found = []

    for i, m in enumerate(pattern.finditer(text)):
        matches_found.append(
            {
                "match_index": i,
                "matched_text": m.group(0),
                "context": extract_context(text, m),
            }
        )

    return {
        "success": True,
        "filepath": filepath,
        "keyword": keyword,
        "match_count": len(matches_found),
        "matches": matches_found,
    }
