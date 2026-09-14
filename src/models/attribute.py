from __future__ import annotations

from pydantic import BaseModel

from src.models.provenance import Provenance


class Attribute(BaseModel):
    name: str
    business_meaning: str
    physical_column: str
    mandatory: bool
    source_of_truth: str
    provenance: Provenance
