from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.data_query import HypothesisQuery, QueryResult
from src.models.profile import TableProfile

MAX_QUERY_LIMIT = 1000


class QueryValidationError(ValueError):
    """Raised when a HypothesisQuery references a table/column outside the domain's
    curated allowlist — never let an LLM-composed query reach real data unchecked."""


class DataSource(ABC):
    """Common interface for the analyst's data checks — read-only, curated tables
    only, every query capped at MAX_QUERY_LIMIT rows.

    Concrete backends (RedshiftDataSource, ExcelDataSource) render and execute a
    HypothesisQuery through their own safe machinery: real parameterized SQL for
    Redshift, direct pandas boolean indexing for Excel — neither ever evaluates
    LLM-authored code or SQL text (spec section 8).
    """

    def __init__(self, allowed_tables: dict[str, list[str]]) -> None:
        """`allowed_tables`: table name -> list of its known column names. Only
        these tables/columns may ever be queried — the domain's curated slice,
        not the whole catalog."""
        self.allowed_tables = allowed_tables

    def _validate(self, query: HypothesisQuery) -> HypothesisQuery:
        if query.table not in self.allowed_tables:
            raise QueryValidationError(f"table not in curated allowlist: {query.table}")
        columns = self.allowed_tables[query.table]
        for f in query.filters:
            if f.column not in columns:
                raise QueryValidationError(f"column not in {query.table}: {f.column}")
        if query.group_by is not None and query.group_by not in columns:
            raise QueryValidationError(f"column not in {query.table}: {query.group_by}")
        if query.aggregate_column is not None and query.aggregate_column not in columns:
            raise QueryValidationError(f"column not in {query.table}: {query.aggregate_column}")
        if query.limit > MAX_QUERY_LIMIT or query.limit <= 0:
            query = query.model_copy(update={"limit": min(max(query.limit, 1), MAX_QUERY_LIMIT)})
        return query

    def list_tables(self) -> list[str]:
        return sorted(self.allowed_tables)

    @abstractmethod
    def preview_query(self, query: HypothesisQuery) -> str:
        """Human-readable text shown to the steward for approval BEFORE run_query."""

    @abstractmethod
    def run_query(self, query: HypothesisQuery) -> QueryResult:
        """Only ever call after the steward has seen preview_query's output and
        explicitly approved it — this method itself does not gate on approval,
        the caller (session/UI layer) does."""

    @abstractmethod
    def profile_table(self, table: str) -> TableProfile:
        """Used by the offline profiling CLI, never live during a session."""
