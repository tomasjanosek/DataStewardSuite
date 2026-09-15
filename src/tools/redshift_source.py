from __future__ import annotations

from src.models.data_query import Aggregate, FilterOp, HypothesisQuery, QueryResult
from src.models.profile import ColumnProfile, TableProfile
from src.tools.data_source import DataSource, QueryValidationError

_FILTER_OPERATORS: dict[FilterOp, str] = {"eq": "=", "ne": "<>", "lt": "<", "lte": "<=", "gt": ">", "gte": ">="}
_AGGREGATE_FUNCTIONS: dict[Aggregate, str] = {"sum": "SUM", "mean": "AVG", "min": "MIN", "max": "MAX"}


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


class RedshiftDataSource(DataSource):
    """Read-only, curated-layer-only access to Redshift for the analyst's
    hypothesis checks (spec section 7). Every query is built from a validated
    HypothesisQuery — table/column names checked against the allowlist before any
    SQL is assembled, filter values always passed as bind parameters, never
    interpolated. `LIMIT` is enforced programmatically.

    # TODO(mvp): UNVERIFIED — no live Redshift cluster was reachable from this
    # session to test an actual connection or query execution. Structurally
    # reviewed against redshift_connector's documented DB-API 2.0 interface, but
    # per spec section 7 ("Over api proti nainstalovane verzi, nepis z pameti")
    # this must be exercised against a real cluster before relying on it —
    # ExcelDataSource is the verified path for a demo.
    """

    def __init__(
        self,
        allowed_tables: dict[str, list[str]],
        *,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        schema: str,
        statement_timeout_ms: int = 30_000,
    ) -> None:
        super().__init__(allowed_tables)
        self._conn_kwargs = {"host": host, "port": port, "database": database, "user": user, "password": password}
        self.schema = schema
        self.statement_timeout_ms = statement_timeout_ms

    def _connect(self):
        import redshift_connector

        conn = redshift_connector.connect(**self._conn_kwargs)
        cur = conn.cursor()
        cur.execute(f"SET statement_timeout = {int(self.statement_timeout_ms)}")
        return conn, cur

    def _aggregate_sql(self, query: HypothesisQuery) -> str:
        if query.aggregate == "count":
            return "COUNT(*)"
        if query.aggregate_column is None:
            raise QueryValidationError("aggregate_column required for this aggregate")
        col = _quote_ident(query.aggregate_column)
        if query.aggregate == "nunique":
            return f"COUNT(DISTINCT {col})"
        return f"{_AGGREGATE_FUNCTIONS[query.aggregate]}({col})"

    def _build_sql(self, query: HypothesisQuery) -> tuple[str, list[object]]:
        table_ident = f"{_quote_ident(self.schema)}.{_quote_ident(query.table)}"
        params: list[object] = []
        where_clauses = []
        for f in query.filters:
            col = _quote_ident(f.column)
            if f.op == "is_null":
                where_clauses.append(f"{col} IS NULL")
            elif f.op == "is_not_null":
                where_clauses.append(f"{col} IS NOT NULL")
            else:
                where_clauses.append(f"{col} {_FILTER_OPERATORS[f.op]} %s")
                params.append(f.value)
        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        agg_sql = self._aggregate_sql(query)
        if query.group_by:
            group_col = _quote_ident(query.group_by)
            sql = f"SELECT {group_col}, {agg_sql} AS value FROM {table_ident}{where_sql} GROUP BY {group_col} LIMIT {query.limit}"
        else:
            sql = f"SELECT {agg_sql} AS value FROM {table_ident}{where_sql}"
        return sql, params

    def preview_query(self, query: HypothesisQuery) -> str:
        query = self._validate(query)
        sql, params = self._build_sql(query)
        for p in params:
            sql = sql.replace("%s", repr(p), 1)
        return sql

    def run_query(self, query: HypothesisQuery) -> QueryResult:
        query = self._validate(query)
        sql, params = self._build_sql(query)
        conn, cur = self._connect()
        try:
            cur.execute(sql, params)
            columns = [d[0] for d in cur.description]
            rows = [list(r) for r in cur.fetchall()]
            return QueryResult(columns=columns, rows=rows, row_count=len(rows), truncated=len(rows) >= query.limit)
        finally:
            conn.close()

    def profile_table(self, table: str) -> TableProfile:
        columns = self.allowed_tables[table]
        table_ident = f"{_quote_ident(self.schema)}.{_quote_ident(table)}"
        conn, cur = self._connect()
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table_ident}")
            row_count = cur.fetchone()[0]

            column_profiles = []
            for col in columns:
                col_ident = _quote_ident(col)
                cur.execute(
                    f"SELECT SUM(CASE WHEN {col_ident} IS NULL THEN 1 ELSE 0 END), "
                    f"COUNT(DISTINCT {col_ident}), MIN({col_ident}), MAX({col_ident}) "
                    f"FROM {table_ident}"
                )
                null_count, distinct_count, min_v, max_v = cur.fetchone()
                null_count = null_count or 0
                column_profiles.append(
                    ColumnProfile(
                        name=col,
                        null_count=null_count,
                        null_pct=(null_count / row_count * 100) if row_count else 0.0,
                        distinct_count=distinct_count or 0,
                        min_value=str(min_v) if min_v is not None else None,
                        max_value=str(max_v) if max_v is not None else None,
                    )
                )
            return TableProfile(table=table, row_count=row_count, columns=column_profiles)
        finally:
            conn.close()
