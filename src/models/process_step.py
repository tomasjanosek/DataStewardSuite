from __future__ import annotations

from pydantic import BaseModel

from src.models.provenance import Provenance


class ProcessStep(BaseModel):
    """One step in how data for an entity comes into being. The heart of the session."""

    # TODO(mvp): id added for milestone 3 — the session needs a stable ref to
    # confirm/reject one specific process step in the UI.
    id: str
    order: int
    actor: str
    system: str
    trigger: str
    action: str
    provenance: Provenance
