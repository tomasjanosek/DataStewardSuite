from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, model_validator

from src.models.provenance import Provenance


class QualityRule(BaseModel):
    id: str
    description_nl: str
    sql: str | None = None
    baseline_result: str | None = None
    baseline_measured_at: datetime | None = None
    proposed_threshold: str | None = None
    owner: str | None = None
    action_on_breach: str | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def _threshold_requires_baseline(self) -> QualityRule:
        if self.proposed_threshold is not None and self.baseline_result is None:
            raise ValueError(
                "proposed_threshold cannot be set before baseline_result is measured"
            )
        return self
