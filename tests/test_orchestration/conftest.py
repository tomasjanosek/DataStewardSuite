from __future__ import annotations

import os

import pytest
from crewai import LLM

from src.models.physical_model import PhysicalColumn, PhysicalModelSlice, PhysicalTable
from src.tools.doc_loader import SourceDocument

requires_llm = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="live LLM test — set ANTHROPIC_API_KEY to run it",
)


@pytest.fixture
def live_llm() -> LLM:
    return LLM(
        model=f"anthropic/{os.environ.get('ANTHROPIC_MODEL', 'claude-haiku-4-5-20251001')}",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        temperature=0,
        max_tokens=8192,
    )


@pytest.fixture
def tiny_model_slice() -> PhysicalModelSlice:
    return PhysicalModelSlice(
        domain="meas",
        tables=[
            PhysicalTable(
                code="MEAS_VAR",
                name="Measuring Variable",
                zone="CORE ZONE",
                folder_path=["CORE ZONE", "Measuring"],
                business_meaning="Jednoznačná proměnná měření (typ, podtyp, účel).",
                table_kind="dimension",
                columns=[
                    PhysicalColumn(
                        code="MEAS_VAR_KEY", name="Measuring Variable Key",
                        data_type="VARCHAR(100)", mandatory=True,
                        business_meaning="Jednoznačný identifikátor proměnné.",
                        stereotype="dw_column",
                    ),
                ],
            ),
            PhysicalTable(
                code="MEAS_FLOW_FACT",
                name="MEAS Flow Fact",
                zone="DATAMARTS",
                folder_path=["DATAMARTS", "DM_MEAS"],
                business_meaning="Naměřený průtok k regulační stanici a proměnné.",
                table_kind="fact",
                columns=[
                    PhysicalColumn(
                        code="VAL", name="Value", data_type="NUMERIC(18,4)",
                        mandatory=True, business_meaning="Naměřená hodnota.",
                        stereotype="dw_column",
                    ),
                ],
                source_tables=["MEAS_VAR"],
            ),
        ],
    )


@pytest.fixture
def tiny_documents() -> list[SourceDocument]:
    return [
        SourceDocument(
            filename="meas-proces-popis.md",
            content=(
                "# Proces měření\n\n"
                "Technik instaluje měřicí zařízení na měřicí místo v systému AVE. "
                "Zařízení pravidelně posílá odečty do SCADA. Aktivní měřicí místo musí "
                "mít vždy přiřazené zařízení, jinak jde o chybu evidence."
            ),
        )
    ]
