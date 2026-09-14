from __future__ import annotations

from typing import Any

import yaml

EMPTY_MARK = "*(žádné položky)*"


def render_frontmatter(fields: dict[str, Any]) -> str:
    return yaml.safe_dump(fields, sort_keys=False, allow_unicode=True).rstrip("\n")


def bullets(items: list[str]) -> list[str]:
    if not items:
        return [EMPTY_MARK]
    return [f"- {item}" for item in items]
