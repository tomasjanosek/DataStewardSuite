from __future__ import annotations

from datetime import datetime

import pytest

from src.models.attribute import Attribute
from src.models.decision import Decision
from src.models.domain_card import DomainCard, EntityRef
from src.models.entity import Entity
from src.models.open_item import OpenItem
from src.models.process_step import ProcessStep
from src.models.provenance import Provenance
from src.models.quality_rule import QualityRule


def _prov(source="document", ref="docs/meas-proces-popis.md", confidence="medium") -> Provenance:
    return Provenance(source=source, ref=ref, confidence=confidence, status="proposed")


@pytest.fixture
def sample_entity() -> Entity:
    return Entity(
        id="meas.mereni-mista",
        name="Měření místa",
        domain="meas",
        business_definition="Fyzické místo, kde se instalací měřicího zařízení odečítá spotřeba.",
        grain="Jeden řádek = jedno měřicí místo.",
        identifier="mereni_mista.id",
        physical_mapping=["meas.mereni_mista"],
        provenance=Provenance(
            source="steward", ref="session:2026-09-14-meas", confidence="high",
            status="confirmed", confirmed_at=datetime(2026, 9, 14, 10, 0),
        ),
        attributes=[
            Attribute(
                name="Stav měřicího místa",
                business_meaning="Zda je místo aktivní, zrušené nebo v přípravě.",
                physical_column="stav",
                mandatory=True,
                source_of_truth="AVE",
                provenance=_prov(),
            )
        ],
        lifecycle=[
            ProcessStep(
                order=1,
                actor="Technik",
                system="AVE",
                trigger="Instalace měřicího zařízení",
                action="Založí nové měřicí místo a napojí ho na zařízení.",
                provenance=_prov(source="steward", ref="session:2026-09-14-meas", confidence="high"),
            )
        ],
        quality_rules=[
            QualityRule(
                id="qr-mereni-mista-1",
                description_nl="Aktivní měřicí místo musí mít přiřazené zařízení.",
                baseline_result="12 z 10 482 aktivních míst bez zařízení",
                baseline_measured_at=datetime(2026, 9, 10, 8, 0),
                proposed_threshold="0 míst bez zařízení",
                owner="Martin Vala",
                provenance=_prov(source="data", ref="query:qr-mereni-mista-1", confidence="high"),
            )
        ],
        known_issues=["Historická data před rokem 2018 nemají vyplněný stav."],
        open_questions=["Co se stane se stavem místa při výměně zařízení?"],
    )


@pytest.fixture
def sample_entity_2() -> Entity:
    return Entity(
        id="meas.odecty",
        name="Odečty",
        domain="meas",
        business_definition="Naměřená hodnota spotřeby k danému měřicímu místu a času.",
        grain="Jeden řádek = jeden odečet jednoho měřicího místa v daném čase.",
        identifier="odecty.id",
        physical_mapping=["meas.odecty"],
        provenance=Provenance(source="document", ref="docs/meas-proces-popis.md", confidence="medium"),
    )


@pytest.fixture
def sample_domain_card() -> DomainCard:
    return DomainCard(
        id="meas",
        name="Měření",
        steward="Martin Vala",
        status="proposed",
        scope_in=["Odečty z měřicích zařízení (SCADA, AVE, Alstanet)"],
        scope_out=["Fakturace na základě měření"],
        source_systems=["SCADA", "AVE", "Alstanet"],
        entities=[
            EntityRef(id="meas.mereni-mista", name="Měření místa", status="confirmed"),
            EntityRef(id="meas.odecty", name="Odečty", status="proposed"),
        ],
        decisions=[
            Decision(
                id="dec-1",
                text="Zrušená měřicí místa se do domény počítají, ale jsou mimo aktivní scope.",
                decided_by="Martin Vala",
                decided_at=datetime(2026, 9, 14, 11, 0),
                provenance=Provenance(
                    source="steward", ref="session:2026-09-14-meas", confidence="high",
                    status="confirmed", confirmed_at=datetime(2026, 9, 14, 11, 0),
                ),
            )
        ],
        open_items=[
            OpenItem(
                id="oi-1",
                text="Kdo je vlastníkem pravidla kvality pro odečty?",
                type="owner_missing",
                raised_at=datetime(2026, 9, 14, 11, 30),
            )
        ],
    )
