from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class EventLog:
    """Append-only sessions/{session_id}/events.jsonl — the source of truth (spec
    section 7). state.json is a derived materialization, never the other way round.
    """

    def __init__(self, sessions_dir: Path | str, session_id: str) -> None:
        self.path = Path(sessions_dir) / session_id / "events.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, **fields: Any) -> None:
        event = {"type": event_type, "at": datetime.now().isoformat(), **fields}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
