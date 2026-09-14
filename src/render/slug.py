from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Turns a name (Czech diacritics included) into a filesystem/wikilink-safe slug.

    "Měření místa" -> "mereni-mista"
    """
    normalized = unicodedata.normalize("NFKD", text)
    without_diacritics = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    lowered = without_diacritics.lower()
    return re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
