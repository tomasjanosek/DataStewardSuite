from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

FilterOp = Literal["eq", "ne", "lt", "lte", "gt", "gte", "is_null", "is_not_null"]
Aggregate = Literal["count", "sum", "mean", "min", "max", "nunique"]


class QueryFilter(BaseModel):
    column: str
    op: FilterOp
    value: str | float | int | bool | None = None


class HypothesisQuery(BaseModel):
    """A steward-approvable, backend-agnostic data check.

    This is the ONLY way the analyst touches data — never raw SQL or code strings
    from the LLM. Each DataSource renders it to its own preview (real SQL for
    Redshift, a plain-language description for the Excel/pandas backend) and
    executes it through safe, parameterized operations — never by evaluating
    LLM-authored text (spec section 8: "Agenti bez code interpreteru a bez pristupu
    k shellu").
    """

    table: str
    description: str  # what this checks, shown to the steward for approval
    filters: list[QueryFilter] = []
    group_by: str | None = None
    aggregate: Aggregate = "count"
    aggregate_column: str | None = None
    limit: int = 100


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list[object]]
    row_count: int
    truncated: bool = False
