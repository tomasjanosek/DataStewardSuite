from __future__ import annotations

from pydantic import BaseModel

from src.models.provenance import Provenance


class Attribute(BaseModel):
    # TODO(mvp): id added for milestone 3 — the session needs a stable ref to
    # confirm/reject one specific attribute in the UI.
    id: str
    name: str
    business_meaning: str
    physical_column: str
    mandatory: bool
    source_of_truth: str
    provenance: Provenance
