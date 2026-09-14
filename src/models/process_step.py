from __future__ import annotations

from pydantic import BaseModel

from src.models.provenance import Provenance


class ProcessStep(BaseModel):
    """One step in how data for an entity comes into being. The heart of the session."""

    order: int
    actor: str
    system: str
    trigger: str
    action: str
    provenance: Provenance
