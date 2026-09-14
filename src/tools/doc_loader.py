from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


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
