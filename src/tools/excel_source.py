from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.models.data_query import HypothesisQuery, QueryResult
from src.models.profile import ColumnProfile, TableProfile
from src.tools.data_source import DataSource, QueryValidationError


def _to_native(value: object) -> object:
    """Converts numpy/pandas scalar types to plain Python so QueryResult rows stay
    JSON-serializable (e.g. for state.json)."""
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            return value
    if pd.isna(value):
        return None
    return value


class ExcelDataSource(DataSource):
    """Offline stand-in for RedshiftDataSource — same HypothesisQuery interface, so
    the analyst crew and the approval UI don't need to know which backend is active.
    Each sheet in the workbook becomes one queryable table. No SQL, no eval: queries
    execute as direct pandas boolean indexing / groupby built from validated
    column names and typed values only.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        sheets = pd.read_excel(self.path, sheet_name=None)
        self._frames: dict[str, pd.DataFrame] = sheets
        allowed = {table: [str(c) for c in df.columns] for table, df in sheets.items()}
        super().__init__(allowed)

    def _apply_filters(self, df: pd.DataFrame, filters: list) -> pd.DataFrame:
        mask = pd.Series(True, index=df.index)
        for f in filters:
            col = df[f.column]
            if f.op == "eq":
                mask &= col == f.value
            elif f.op == "ne":
                mask &= col != f.value
            elif f.op == "lt":
                mask &= col < f.value
            elif f.op == "lte":
                mask &= col <= f.value
            elif f.op == "gt":
                mask &= col > f.value
            elif f.op == "gte":
                mask &= col >= f.value
            elif f.op == "is_null":
                mask &= col.isna()
            elif f.op == "is_not_null":
                mask &= col.notna()
        return df[mask]

    def preview_query(self, query: HypothesisQuery) -> str:
        query = self._validate(query)
        lines = [f"List: {query.table}", f"Účel: {query.description}"]
        if query.filters:
            lines.append("Filtr:")
            for f in query.filters:
                value = "" if f.value is None else f.value
                lines.append(f"  - {f.column} {f.op} {value}")
        if query.group_by:
            lines.append(f"Seskupit podle: {query.group_by}")
        agg = query.aggregate + (f"({query.aggregate_column})" if query.aggregate_column else "")
        lines.append(f"Agregace: {agg}")
        lines.append(f"Limit: {query.limit}")
        return "\n".join(lines)

    def run_query(self, query: HypothesisQuery) -> QueryResult:
        query = self._validate(query)
        filtered = self._apply_filters(self._frames[query.table], query.filters)

        if query.group_by:
            grouped = filtered.groupby(query.group_by)
            if query.aggregate == "count":
                result = grouped.size().reset_index(name="count")
            elif query.aggregate_column is None:
                raise QueryValidationError("aggregate_column required for this aggregate")
            elif query.aggregate == "nunique":
                result = grouped[query.aggregate_column].nunique().reset_index(name="nunique")
            else:
                result = getattr(grouped[query.aggregate_column], query.aggregate)().reset_index(name=query.aggregate)
            result = result.head(query.limit)
            rows = [[_to_native(v) for v in row] for row in result.values.tolist()]
            return QueryResult(
                columns=[str(c) for c in result.columns], rows=rows,
                row_count=len(result), truncated=len(result) >= query.limit,
            )

        if query.aggregate == "count" and query.aggregate_column is None:
            total = len(filtered)
            preview = filtered.head(query.limit)
            rows = [[_to_native(v) for v in row] for row in preview.values.tolist()]
            return QueryResult(
                columns=[str(c) for c in preview.columns], rows=rows,
                row_count=total, truncated=total > query.limit,
            )

        if query.aggregate_column is None:
            raise QueryValidationError("aggregate_column required for this aggregate")
        value = getattr(filtered[query.aggregate_column], query.aggregate)()
        return QueryResult(columns=[query.aggregate], rows=[[_to_native(value)]], row_count=1)

    def profile_table(self, table: str) -> TableProfile:
        df = self._frames[table]
        columns = []
        for name in df.columns:
            col = df[name]
            non_null = col.dropna()
            columns.append(
                ColumnProfile(
                    name=str(name),
                    null_count=int(col.isna().sum()),
                    null_pct=float(col.isna().mean() * 100),
                    distinct_count=int(col.nunique()),
                    min_value=str(non_null.min()) if not non_null.empty else None,
                    max_value=str(non_null.max()) if not non_null.empty else None,
                )
            )
        return TableProfile(table=table, row_count=len(df), columns=columns)
