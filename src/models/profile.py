from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ColumnProfile(BaseModel):
    name: str
    null_count: int
    null_pct: float
    distinct_count: int
    min_value: str | None = None
    max_value: str | None = None


class TableProfile(BaseModel):
    table: str
    row_count: int
    columns: list[ColumnProfile] = []
    # TODO(mvp): orphan detection (FK values with no matching parent row) needs
    # relationship metadata beyond what model_loader captures — not implemented.


class DataProfile(BaseModel):
    """Precomputed offline (spec section 7: profiling never runs live during a
    session), one file per domain, source of the `baseline_result` a steward-approved
    hypothesis check fills into a QualityRule.
    """

    domain: str
    measured_at: datetime
    tables: list[TableProfile] = []
