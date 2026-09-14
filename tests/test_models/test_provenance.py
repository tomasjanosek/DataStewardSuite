from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.provenance import Provenance


def test_confirmed_requires_confirmed_at():
    with pytest.raises(ValidationError):
        Provenance(source="steward", ref="session:2026-09-14-meas", confidence="high", status="confirmed")


def test_rejected_requires_reason():
    with pytest.raises(ValidationError):
        Provenance(source="steward", ref="session:2026-09-14-meas", confidence="high", status="rejected")


def test_draft_needs_no_extra_fields():
    prov = Provenance(source="document", ref="docs/meas.md", confidence="medium")
    assert prov.status == "draft"


def test_confirm_helper_sets_status_and_timestamp_without_mutating_original():
    prov = Provenance(source="document", ref="docs/meas.md", confidence="medium")
    confirmed = prov.confirm(at=datetime(2026, 9, 14, 10, 0))

    assert confirmed.status == "confirmed"
    assert confirmed.confirmed_at == datetime(2026, 9, 14, 10, 0)
    assert prov.status == "draft"


def test_reject_helper_requires_reason_argument():
    prov = Provenance(source="data", ref="query:123", confidence="medium")
    rejected = prov.reject("Odpovídá jinému výpočtu, steward to nepotvrdil.")

    assert rejected.status == "rejected"
    assert rejected.rejection_reason
