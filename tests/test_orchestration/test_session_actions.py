from __future__ import annotations

import pytest

from src.models.lead_turn import LeadTurnResult, ProposedAttribute, ProposedDecision, ProposedOpenItem, ProposedProcessStep
from src.orchestration.session_actions import (
    apply_lead_proposals,
    compute_coverage,
    confirm_attribute,
    confirm_decision,
    confirm_entity,
    confirm_process_step,
    confirm_scope_item,
    new_session_state,
    reject_attribute,
    reject_entity,
    reject_scope_item,
)
from src.tools.event_log import EventLog


@pytest.fixture
def state(sample_config, sample_variant):
    return new_session_state("2026-09-15-meas", sample_config, sample_variant)


@pytest.fixture
def event_log(tmp_path):
    return EventLog(tmp_path, "2026-09-15-meas")


def test_new_session_state_seeds_scope_and_entities_as_proposed(state):
    assert len(state.domain_card.scope_in) == 1
    assert state.domain_card.scope_in[0].provenance.status == "proposed"
    assert len(state.entities) == 2
    for entity in state.entities.values():
        assert entity.provenance.status == "proposed"
    assert {ref.status for ref in state.domain_card.entities} == {"proposed"}


def test_confirm_scope_item_sets_confirmed_and_snapshots(state, event_log):
    item_id = state.domain_card.scope_in[0].id
    confirm_scope_item(state, "scope_in", item_id, event_log)

    assert state.domain_card.scope_in[0].provenance.status == "confirmed"
    assert state.domain_card.scope_in[0].provenance.confirmed_at is not None
    assert state.last_confirmed_snapshot is not None
    events = event_log.read_all()
    assert events[-1]["type"] == "confirm"
    assert events[-1]["ref"] == item_id


def test_reject_scope_item_requires_and_stores_reason(state, event_log):
    item_id = state.domain_card.scope_out[0].id
    reject_scope_item(state, "scope_out", item_id, "Steward: mimo rozsah.", event_log)

    item = state.domain_card.scope_out[0]
    assert item.provenance.status == "rejected"
    assert item.provenance.rejection_reason == "Steward: mimo rozsah."
    events = event_log.read_all()
    assert events[-1]["reason"] == "Steward: mimo rozsah."


def test_confirm_and_reject_entity(state, event_log):
    entity_id = next(iter(state.entities))
    confirm_entity(state, entity_id, event_log)
    assert state.entities[entity_id].provenance.status == "confirmed"
    assert next(r for r in state.domain_card.entities if r.id == entity_id).status == "confirmed"


def test_reject_entity_never_leaves_it_confirmed(state, event_log):
    entity_id = next(iter(state.entities))
    reject_entity(state, entity_id, "Duplicitní s jinou entitou.", event_log)
    assert state.entities[entity_id].provenance.status == "rejected"
    assert next(r for r in state.domain_card.entities if r.id == entity_id).status == "rejected"


def test_apply_lead_proposals_are_always_proposed_never_confirmed(state, event_log):
    entity_id = next(iter(state.entities))
    turn = LeadTurnResult(
        reply="Rozumím, zapíšu si to.",
        proposed_attributes=[
            ProposedAttribute(
                entity_id=entity_id, name="Stav", business_meaning="Stav místa.",
                physical_column="stav", mandatory=True, source_of_truth="AVE",
                source="steward", ref="session:2026-09-15-meas", confidence="medium",
            )
        ],
        proposed_process_steps=[
            ProposedProcessStep(
                entity_id=entity_id, order=1, actor="Technik", system="AVE",
                trigger="Instalace", action="Založí měřicí místo.",
                source="steward", ref="session:2026-09-15-meas", confidence="high",
            )
        ],
        proposed_decisions=[
            ProposedDecision(
                text="Zrušená místa zůstávají v evidenci.",
                source="inference", ref="session:2026-09-15-meas", confidence="low",
            )
        ],
        proposed_open_items=[
            ProposedOpenItem(text="Kdo je vlastníkem procesu?", type="owner_missing"),
        ],
    )

    apply_lead_proposals(state, turn, state.id, event_log)

    entity = state.entities[entity_id]
    assert entity.attributes[0].provenance.status == "proposed"
    assert entity.lifecycle[0].provenance.status == "proposed"
    assert state.domain_card.decisions[0].provenance.status == "proposed"
    assert state.domain_card.open_items[0].text == "Kdo je vlastníkem procesu?"


def test_confirm_attribute_and_process_step_after_proposal(state, event_log):
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
        proposed_process_steps=[
            ProposedProcessStep(
                entity_id=entity_id, order=1, actor="Technik", system="AVE",
                trigger="Instalace", action="Založí měřicí místo.",
                source="steward", ref="session:x", confidence="high",
            )
        ],
    )
    apply_lead_proposals(state, turn, state.id, event_log)

    attr_id = state.entities[entity_id].attributes[0].id
    step_id = state.entities[entity_id].lifecycle[0].id

    confirm_attribute(state, entity_id, attr_id, event_log)
    confirm_process_step(state, entity_id, step_id, event_log)

    assert state.entities[entity_id].attributes[0].provenance.status == "confirmed"
    assert state.entities[entity_id].lifecycle[0].provenance.status == "confirmed"


def test_reject_attribute_stores_reason_and_never_confirms(state, event_log):
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
    apply_lead_proposals(state, turn, state.id, event_log)
    attr_id = state.entities[entity_id].attributes[0].id

    reject_attribute(state, entity_id, attr_id, "Duplicita s jiným atributem.", event_log)

    attr = state.entities[entity_id].attributes[0]
    assert attr.provenance.status == "rejected"
    assert attr.provenance.rejection_reason == "Duplicita s jiným atributem."


def test_compute_coverage_increases_as_items_are_confirmed(state, event_log):
    before = compute_coverage(state)
    item_id = state.domain_card.scope_in[0].id
    confirm_scope_item(state, "scope_in", item_id, event_log)
    after = compute_coverage(state)
    assert after > before


def test_confirm_decision_after_proposal(state, event_log):
    turn = LeadTurnResult(
        reply="ok",
        proposed_decisions=[
            ProposedDecision(text="Test decision.", source="steward", ref="session:x", confidence="high")
        ],
    )
    apply_lead_proposals(state, turn, state.id, event_log)
    decision_id = state.domain_card.decisions[0].id

    confirm_decision(state, decision_id, event_log)

    assert state.domain_card.decisions[0].provenance.status == "confirmed"
