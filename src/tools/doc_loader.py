from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel

_ALLOWED_DOC_SUFFIXES = (".md", ".txt")
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")


class SourceDocument(BaseModel):
    filename: str
    content: str


def load_documents(docs_dir: Path | str, filenames: list[str]) -> list[SourceDocument]:
    """Loads background documents straight into context. No vector DB / RAG —
    see spec section 2, "Co MVP vedome neumi"."""
    docs_dir = Path(docs_dir)
    return [
        SourceDocument(filename=filename, content=(docs_dir / filename).read_text(encoding="utf-8"))
        for filename in filenames
    ]


def list_available_documents(docs_dir: Path | str) -> list[str]:
    docs_dir = Path(docs_dir)
    if not docs_dir.exists():
        return []
    return sorted(p.name for p in docs_dir.iterdir() if p.is_file() and p.suffix.lower() in _ALLOWED_DOC_SUFFIXES)


def sanitize_filename(name: str) -> str:
    """Strips any directory components and restricts to a safe character set —
    steward-uploaded filenames are untrusted input, this prevents path traversal."""
    base = Path(name).name
    base = _UNSAFE_FILENAME_CHARS.sub("_", base)
    return base if base and base not in (".", "..") else "upload.txt"
