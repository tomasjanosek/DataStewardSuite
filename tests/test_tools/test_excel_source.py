from __future__ import annotations

import pandas as pd
import pytest

from src.models.data_query import HypothesisQuery, QueryFilter
from src.tools.data_source import QueryValidationError
from src.tools.excel_source import ExcelDataSource


@pytest.fixture
def excel_path(tmp_path):
    path = tmp_path / "meas.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "stav": ["aktivni", "aktivni", "zruseno", "aktivni", None],
                "zarizeni_id": [10, None, 30, 40, 50],
            }
        ).to_excel(writer, sheet_name="mereni_mista", index=False)
        pd.DataFrame({"id": [1, 2], "hodnota": [12.5, -3.0]}).to_excel(writer, sheet_name="odecty", index=False)
    return path


@pytest.fixture
def source(excel_path):
    return ExcelDataSource(excel_path)


def test_list_tables_matches_sheet_names(source):
    assert set(source.list_tables()) == {"mereni_mista", "odecty"}


def test_rejects_unknown_table(source):
    query = HypothesisQuery(table="does_not_exist", description="x")
    with pytest.raises(QueryValidationError):
        source.run_query(query)


def test_rejects_unknown_column(source):
    query = HypothesisQuery(
        table="mereni_mista", description="x", filters=[QueryFilter(column="nope", op="eq", value=1)]
    )
    with pytest.raises(QueryValidationError):
        source.run_query(query)


def test_count_with_filter(source):
    query = HypothesisQuery(
        table="mereni_mista",
        description="Aktivní místa bez zařízení.",
        filters=[
            QueryFilter(column="stav", op="eq", value="aktivni"),
            QueryFilter(column="zarizeni_id", op="is_null"),
        ],
    )
    result = source.run_query(query)
    assert result.row_count == 1


def test_groupby_count(source):
    query = HypothesisQuery(table="mereni_mista", description="Rozdělení podle stavu.", group_by="stav")
    result = source.run_query(query)
    assert result.columns == ["stav", "count"]
    # pandas groupby drops the NaN group by default, so only aktivni/zruseno appear
    assert result.row_count == 2


def test_scalar_aggregate(source):
    query = HypothesisQuery(
        table="odecty", description="Součet hodnot.", aggregate="sum", aggregate_column="hodnota"
    )
    result = source.run_query(query)
    assert result.rows[0][0] == pytest.approx(9.5)


def test_preview_query_is_readable_text(source):
    query = HypothesisQuery(
        table="mereni_mista",
        description="Aktivní místa bez zařízení.",
        filters=[QueryFilter(column="stav", op="eq", value="aktivni")],
    )
    preview = source.preview_query(query)
    assert "mereni_mista" in preview
    assert "stav" in preview
    assert "Aktivní místa bez zařízení." in preview


def test_profile_table_reports_nulls_and_distinct(source):
    profile = source.profile_table("mereni_mista")
    assert profile.row_count == 5
    stav_col = next(c for c in profile.columns if c.name == "stav")
    assert stav_col.null_count == 1
    assert stav_col.distinct_count == 2
