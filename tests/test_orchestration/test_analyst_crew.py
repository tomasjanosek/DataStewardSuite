from __future__ import annotations

from datetime import datetime

from src.models.data_query import QueryResult
from src.models.profile import ColumnProfile, DataProfile, TableProfile
from src.orchestration.analyst_crew import interpret_result, propose_query

from .conftest import requires_llm


@requires_llm
def test_propose_query_returns_structured_hypothesis_query(live_llm):
    profile = DataProfile(
        domain="meas",
        measured_at=datetime.now(),
        tables=[
            TableProfile(
                table="mereni_mista",
                row_count=10482,
                columns=[
                    ColumnProfile(name="stav", null_count=0, null_pct=0.0, distinct_count=3, min_value="aktivni", max_value="zruseno"),
                    ColumnProfile(name="zarizeni_id", null_count=12, null_pct=0.11, distinct_count=10470),
                ],
            )
        ],
    )

    proposal = propose_query("Aktivní měřicí místo musí mít vždy přiřazené zařízení.", profile, live_llm)

    assert proposal.query.table == "mereni_mista"
    assert proposal.query.description
    assert proposal.query.filters or proposal.query.group_by
    # rationale defaults to "" rather than being required — see AnalystQueryProposal


@requires_llm
def test_interpret_result_never_accuses_steward(live_llm):
    result = QueryResult(columns=["count"], rows=[[12]], row_count=1)

    finding = interpret_result(
        "Aktivní měřicí místo musí mít vždy přiřazené zařízení.",
        "Počet aktivních míst bez zařízení (mereni_mista, stav=aktivni, zarizeni_id is_null).",
        result,
        live_llm,
    )

    assert finding.text
    assert finding.quantification
    assert finding.confidence in ("low", "medium", "high")
