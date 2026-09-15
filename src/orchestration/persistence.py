from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.flow.persistence.base import FlowPersistence
from pydantic import BaseModel


class JsonFileFlowPersistence(FlowPersistence):
    """Writes sessions/{flow_uuid}/state.json — the materialization of SessionState
    (spec section 7: "state.json je materializace", events.jsonl is the source of
    truth). One JSON file per session, always overwritten with the latest snapshot;
    no history is kept here (events.jsonl has that).

    # TODO(mvp): crewai 0.203.2's `@persist()` binds its persistence instance at
    # class-decoration time (a closure over the argument passed to the decorator,
    # not read from the Flow instance) — so the same JsonFileFlowPersistence object
    # must back every SessionFlow. `configure()` repoints the *directory* that
    # singleton writes to, without needing a second instance (verified empirically:
    # passing a fresh instance per Flow construction silently fell back to crewai's
    # default SQLiteFlowPersistence instead).
    """

    _sessions_dir: Path = Path("sessions")

    @classmethod
    def configure(cls, sessions_dir: Path | str) -> None:
        cls._sessions_dir = Path(sessions_dir)

    def init_db(self) -> None:
        type(self)._sessions_dir.mkdir(parents=True, exist_ok=True)

    def _state_path(self, flow_uuid: str) -> Path:
        return type(self)._sessions_dir / flow_uuid / "state.json"

    def save_state(self, flow_uuid: str, method_name: str, state_data: dict[str, Any] | BaseModel) -> None:
        data = state_data.model_dump(mode="json") if isinstance(state_data, BaseModel) else state_data
        path = self._state_path(flow_uuid)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_state(self, flow_uuid: str) -> dict[str, Any] | None:
        path = self._state_path(flow_uuid)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))


# Singleton required by @persist()'s decoration-time binding — see docstring above.
SHARED_PERSISTENCE = JsonFileFlowPersistence()
