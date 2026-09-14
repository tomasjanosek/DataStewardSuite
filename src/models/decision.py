from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from src.models.provenance import Provenance


class Decision(BaseModel):
    # TODO(mvp): spec section 4 references `decisions: list[Decision]` on DomainCard
    # but never defines the Decision shape. Fields below are the minimal set inferred
    # from context (section 6, phase 7: "rozhodnuti, vlastnici, otevrene body").
    id: str
    text: str
    decided_by: str
    decided_at: datetime
    provenance: Provenance
