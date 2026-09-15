from __future__ import annotations

import pytest

from src.models.lead_turn import LeadTurnResult, ProposedAttribute
from src.orchestration.resume import build_resume_summary
from src.orchestration.session_actions import apply_lead_proposals, confirm_scope_item, new_session_state
from src.tools.event_log import EventLog


@pytest.fixture
def state(sample_config, sample_variant):
    return new_session_state("2026-09-15-meas", sample_config, sample_variant)


@pytest.fixture
def event_log(tmp_path):
    return EventLog(tmp_path, "2026-09-15-meas")


def test_resume_summary_lists_nothing_confirmed_on_fresh_session(state):
    summary = build_resume_summary(state)
    assert "*(zatím nic)*" in summary
    assert "*(nic nového)*" in summary


def test_resume_summary_shows_confirmed_scope_item(state, event_log):
    item_id = state.domain_card.scope_in[0].id
    confirm_scope_item(state, "scope_in", item_id, event_log)

    summary = build_resume_summary(state)
    assert state.domain_card.scope_in[0].text in summary
    assert "Patří do domény" in summary


def test_resume_summary_shows_pending_proposal_since_last_confirmation(state, event_log):
    item_id = state.domain_card.scope_in[0].id
    confirm_scope_item(state, "scope_in", item_id, event_log)  # takes a snapshot

    entity_id = next(iter(state.entities))
    turn = LeadTurnResult(
        reply="ok",
        proposed_attributes=[
            ProposedAttribute(
                entity_id=entity_id, name="Stav", business_meaning="Stav místa.",
                physical_column="stav", mandatory=True, source_of_truth="AVE",
                source="steward", ref="session:x", confidence="medium",
            )
        ],
    )
    apply_lead_proposals(state, turn, state.id, event_log)  # NOT confirmed, no new snapshot

    summary = build_resume_summary(state)
    assert "čeká na rozhodnutí" in summary
    assert "Stav" in summary
    assert "*(nic nového)*" not in summary
