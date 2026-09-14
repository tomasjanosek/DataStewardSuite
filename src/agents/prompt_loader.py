from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Loads a prompt template by filename (e.g. "architect_role.md").

    Prompts live in separate files, not in code — see spec section 13, they change daily.
    """
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")
