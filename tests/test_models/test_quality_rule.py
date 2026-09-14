from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.provenance import Provenance
from src.models.quality_rule import QualityRule


def _provenance() -> Provenance:
    return Provenance(source="data", ref="query:qr-1", confidence="medium")


def test_threshold_without_baseline_is_rejected():
    with pytest.raises(ValidationError):
        QualityRule(
            id="qr-1",
            description_nl="Odečet nesmí být záporný.",
            proposed_threshold=">= 0",
            provenance=_provenance(),
        )


def test_threshold_with_baseline_is_accepted():
    rule = QualityRule(
        id="qr-1",
        description_nl="Odečet nesmí být záporný.",
        baseline_result="0 záporných záznamů z 10 000",
        proposed_threshold=">= 0",
        provenance=_provenance(),
    )
    assert rule.proposed_threshold == ">= 0"


def test_baseline_without_threshold_is_fine():
    rule = QualityRule(
        id="qr-1",
        description_nl="Odečet nesmí být záporný.",
        baseline_result="0 záporných záznamů z 10 000",
        provenance=_provenance(),
    )
    assert rule.proposed_threshold is None
