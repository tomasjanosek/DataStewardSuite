from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

ProvenanceSource = Literal["physical_model", "document", "data", "steward", "inference"]
ProvenanceConfidence = Literal["low", "medium", "high"]
ProvenanceStatus = Literal["draft", "proposed", "confirmed", "rejected"]


class Provenance(BaseModel):
    """Tracks where a claim came from and whether the steward has confirmed it.

    Rule: status "confirmed" may only be reached through steward confirmation in a
    live session. Agents may propose at most. This is enforced by convention for the
    MVP: orchestration code must only ever call .confirm() from the session's
    confirmation handler, never construct Provenance(status="confirmed", ...) directly
    on an agent's behalf.
    # TODO(mvp): a stricter guarantee would need Provenance construction restricted to
    # a bounded module; not worth the complexity for a single-process MVP.
    """

    source: ProvenanceSource
    ref: str
    confidence: ProvenanceConfidence
    status: ProvenanceStatus = "draft"
    rejection_reason: str | None = None
    confirmed_at: datetime | None = None

    @model_validator(mode="after")
    def _check_status_invariants(self) -> Provenance:
        if self.status == "rejected" and not self.rejection_reason:
            raise ValueError("rejection_reason is required when status is 'rejected'")
        if self.status == "confirmed" and self.confirmed_at is None:
            raise ValueError("confirmed_at is required when status is 'confirmed'")
        return self

    def propose(self) -> Provenance:
        return self.model_copy(update={"status": "proposed"})

    def confirm(self, at: datetime | None = None) -> Provenance:
        return self.model_copy(update={"status": "confirmed", "confirmed_at": at or datetime.now()})

    def reject(self, reason: str) -> Provenance:
        return self.model_copy(update={"status": "rejected", "rejection_reason": reason})
