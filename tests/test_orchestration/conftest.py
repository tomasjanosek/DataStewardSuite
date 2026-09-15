from __future__ import annotations

import os

import pytest
from crewai import LLM

from src.models.physical_model import PhysicalColumn, PhysicalModelSlice, PhysicalTable
from src.models.strawman import ConceptualEntityProposal, ModelVariant, SourcedClaim
from src.tools.doc_loader import SourceDocument
from src.tools.domain_config import DomainConfig, ModelScope

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
def sample_config() -> DomainConfig:
    return DomainConfig(
        domain="meas",
        name="Měření",
        steward="Martin Vala",
        goal="Popsat proces vzniku dat o měření a potvrdit klíčové entity.",
        scope_in=["Odečty z měřicích zařízení (SCADA, AVE, Alstanet)"],
        scope_out=["Fakturace na základě měření"],
        model_scope=ModelScope(folders=["CORE ZONE > Measuring"], table_code_patterns=["^LZ_SCADA_"]),
        documents=[],
        what_would_prove_us_wrong="Kdyby korekce hodnot probíhala mimo evidovaný proces.",
    )


@pytest.fixture
def sample_variant() -> ModelVariant:
    return ModelVariant(
        label="Varianta A",
        description="Jedna entita na jednu core tabulku.",
        consequences="Jednoduché, blízké fyzickému modelu.",
        entities=[
            ConceptualEntityProposal(
                name="Měřicí místo",
                grain="Jeden řádek = jedno měřicí místo.",
                physical_mapping=["MEAS_VAR"],
                rationale=SourcedClaim(
                    text="MEAS_VAR nese jednoznačný identifikátor měřicího místa.",
                    source="physical_model", ref="MEAS_VAR", confidence="high",
                ),
            ),
            ConceptualEntityProposal(
                name="Odečet",
                grain="Jeden řádek = jeden odečet.",
                physical_mapping=["MEAS_FLOW_FACT"],
                rationale=SourcedClaim(
                    text="MEAS_FLOW_FACT nese naměřenou hodnotu k proměnné a periodě.",
                    source="physical_model", ref="MEAS_FLOW_FACT", confidence="medium",
                ),
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
