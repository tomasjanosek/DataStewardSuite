from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from src.models.attribute import Attribute
from src.models.decision import Decision
from src.models.domain_card import DomainCard, EntityRef, ScopeStatement
from src.models.entity import Entity
from src.models.lead_turn import LeadTurnResult
from src.models.open_item import OpenItem
from src.models.process_step import ProcessStep
from src.models.provenance import Provenance, ProvenanceConfidence
from src.models.quality_rule import QualityRule
from src.models.session import SessionState
from src.models.strawman import ModelVariant
from src.render.slug import slugify
from src.tools.domain_config import DomainConfig
from src.tools.event_log import EventLog

ScopeDirection = Literal["scope_in", "scope_out"]


def new_session_state(session_id: str, config: DomainConfig, variant: ModelVariant) -> SessionState:
    """Seeds a fresh SessionState from the domain config (scope_in/out) and the
    architect variant chosen at the REVIEW gate. Everything starts `proposed` — only
    a steward's live confirmation (see confirm_* below) can promote it further.
    """
    config_ref = f"config/domains/{config.domain}.yaml"

    def _scope_statements(texts: list[str], prefix: str) -> list[ScopeStatement]:
        return [
            ScopeStatement(
                id=f"{prefix}-{i}",
                text=text,
                provenance=Provenance(source="document", ref=config_ref, confidence="medium", status="proposed"),
            )
            for i, text in enumerate(texts, start=1)
        ]

    entities: dict[str, Entity] = {}
    entity_refs: list[EntityRef] = []
    for proposal in variant.entities:
        entity_id = slugify(proposal.name)
        entities[entity_id] = Entity(
            id=entity_id,
            name=proposal.name,
            domain=config.domain,
            business_definition=proposal.rationale.text,
            grain=proposal.grain,
            identifier="",
            physical_mapping=list(proposal.physical_mapping),
            provenance=Provenance(
                source=proposal.rationale.source,
                ref=proposal.rationale.ref,
                confidence=proposal.rationale.confidence,
                status="proposed",
            ),
        )
        entity_refs.append(EntityRef(id=entity_id, name=proposal.name, status="proposed"))

    domain_card = DomainCard(
        id=config.domain,
        name=config.name,
        steward=config.steward,
        status="draft",
        scope_in=_scope_statements(config.scope_in, "scope-in"),
        scope_out=_scope_statements(config.scope_out, "scope-out"),
        entities=entity_refs,
    )
    return SessionState(id=session_id, domain=config.domain, domain_card=domain_card, entities=entities)


def _snapshot(state: SessionState) -> None:
    """Records the artifact as of the latest confirmation/rejection, for the resume
    diff (spec section 6)."""
    state.last_confirmed_snapshot = {
        "domain_card": state.domain_card.model_dump(mode="json"),
        "entities": {k: v.model_dump(mode="json") for k, v in state.entities.items()},
    }


def confirm_scope_item(state: SessionState, direction: ScopeDirection, item_id: str, event_log: EventLog) -> None:
    items = state.domain_card.scope_in if direction == "scope_in" else state.domain_card.scope_out
    for i, item in enumerate(items):
        if item.id == item_id:
            items[i] = item.model_copy(update={"provenance": item.provenance.confirm()})
            event_log.append("confirm", kind=direction, ref=item_id, text=item.text)
            _snapshot(state)
            return
    raise ValueError(f"{direction} item not found: {item_id}")


def reject_scope_item(
    state: SessionState, direction: ScopeDirection, item_id: str, reason: str, event_log: EventLog
) -> None:
    items = state.domain_card.scope_in if direction == "scope_in" else state.domain_card.scope_out
    for i, item in enumerate(items):
        if item.id == item_id:
            items[i] = item.model_copy(update={"provenance": item.provenance.reject(reason)})
            event_log.append("reject", kind=direction, ref=item_id, text=item.text, reason=reason)
            _snapshot(state)
            return
    raise ValueError(f"{direction} item not found: {item_id}")


def confirm_entity(state: SessionState, entity_id: str, event_log: EventLog) -> None:
    entity = state.entities[entity_id]
    state.entities[entity_id] = entity.model_copy(update={"provenance": entity.provenance.confirm()})
    for i, ref in enumerate(state.domain_card.entities):
        if ref.id == entity_id:
            state.domain_card.entities[i] = ref.model_copy(update={"status": "confirmed"})
    event_log.append("confirm", kind="entity", ref=entity_id, text=entity.name)
    _snapshot(state)


def reject_entity(state: SessionState, entity_id: str, reason: str, event_log: EventLog) -> None:
    entity = state.entities[entity_id]
    state.entities[entity_id] = entity.model_copy(update={"provenance": entity.provenance.reject(reason)})
    for i, ref in enumerate(state.domain_card.entities):
        if ref.id == entity_id:
            state.domain_card.entities[i] = ref.model_copy(update={"status": "rejected"})
    event_log.append("reject", kind="entity", ref=entity_id, text=entity.name, reason=reason)
    _snapshot(state)


def _confirm_in_list(items: list, item_id: str) -> bool:
    for i, item in enumerate(items):
        if item.id == item_id:
            items[i] = item.model_copy(update={"provenance": item.provenance.confirm()})
            return True
    return False


def _reject_in_list(items: list, item_id: str, reason: str) -> bool:
    for i, item in enumerate(items):
        if item.id == item_id:
            items[i] = item.model_copy(update={"provenance": item.provenance.reject(reason)})
            return True
    return False


def confirm_attribute(state: SessionState, entity_id: str, attribute_id: str, event_log: EventLog) -> None:
    entity = state.entities[entity_id]
    if not _confirm_in_list(entity.attributes, attribute_id):
        raise ValueError(f"attribute not found: {attribute_id}")
    event_log.append("confirm", kind="attribute", entity_id=entity_id, ref=attribute_id)
    _snapshot(state)


def reject_attribute(state: SessionState, entity_id: str, attribute_id: str, reason: str, event_log: EventLog) -> None:
    entity = state.entities[entity_id]
    if not _reject_in_list(entity.attributes, attribute_id, reason):
        raise ValueError(f"attribute not found: {attribute_id}")
    event_log.append("reject", kind="attribute", entity_id=entity_id, ref=attribute_id, reason=reason)
    _snapshot(state)


def confirm_process_step(state: SessionState, entity_id: str, step_id: str, event_log: EventLog) -> None:
    entity = state.entities[entity_id]
    if not _confirm_in_list(entity.lifecycle, step_id):
        raise ValueError(f"process step not found: {step_id}")
    event_log.append("confirm", kind="process_step", entity_id=entity_id, ref=step_id)
    _snapshot(state)


def reject_process_step(state: SessionState, entity_id: str, step_id: str, reason: str, event_log: EventLog) -> None:
    entity = state.entities[entity_id]
    if not _reject_in_list(entity.lifecycle, step_id, reason):
        raise ValueError(f"process step not found: {step_id}")
    event_log.append("reject", kind="process_step", entity_id=entity_id, ref=step_id, reason=reason)
    _snapshot(state)


def confirm_decision(state: SessionState, decision_id: str, event_log: EventLog) -> None:
    if not _confirm_in_list(state.domain_card.decisions, decision_id):
        raise ValueError(f"decision not found: {decision_id}")
    event_log.append("confirm", kind="decision", ref=decision_id)
    _snapshot(state)


def reject_decision(state: SessionState, decision_id: str, reason: str, event_log: EventLog) -> None:
    if not _reject_in_list(state.domain_card.decisions, decision_id, reason):
        raise ValueError(f"decision not found: {decision_id}")
    event_log.append("reject", kind="decision", ref=decision_id, reason=reason)
    _snapshot(state)


def apply_lead_proposals(state: SessionState, turn: LeadTurnResult, session_id: str, event_log: EventLog) -> None:
    """Materializes the lead's proposals onto the artifact. Always status="proposed"
    (or, for OpenItem which carries no provenance, its normal initial "open") — this
    function is the ONLY place lead output turns into artifact content, so it is the
    single point that guarantees an agent can never write "confirmed" (spec's core
    invariant, acceptance criterion #8).
    """
    for a in turn.proposed_attributes:
        entity = state.entities.get(a.entity_id)
        if entity is None:
            continue
        entity.attributes.append(
            Attribute(
                id=f"attr-{uuid.uuid4().hex[:8]}",
                name=a.name,
                business_meaning=a.business_meaning,
                physical_column=a.physical_column,
                mandatory=a.mandatory,
                source_of_truth=a.source_of_truth,
                provenance=Provenance(source=a.source, ref=a.ref, confidence=a.confidence, status="proposed"),
            )
        )
        event_log.append("propose", kind="attribute", entity_id=a.entity_id, name=a.name)

    for p in turn.proposed_process_steps:
        entity = state.entities.get(p.entity_id)
        if entity is None:
            continue
        entity.lifecycle.append(
            ProcessStep(
                id=f"step-{uuid.uuid4().hex[:8]}",
                order=p.order,
                actor=p.actor,
                system=p.system,
                trigger=p.trigger,
                action=p.action,
                provenance=Provenance(source=p.source, ref=p.ref, confidence=p.confidence, status="proposed"),
            )
        )
        event_log.append("propose", kind="process_step", entity_id=p.entity_id, action=p.action)

    for d in turn.proposed_decisions:
        state.domain_card.decisions.append(
            Decision(
                id=f"dec-{uuid.uuid4().hex[:8]}",
                text=d.text,
                decided_by=state.domain_card.steward,
                decided_at=datetime.now(),
                provenance=Provenance(source=d.source, ref=d.ref, confidence=d.confidence, status="proposed"),
            )
        )
        event_log.append("propose", kind="decision", text=d.text)

    for o in turn.proposed_open_items:
        state.domain_card.open_items.append(
            OpenItem(
                id=f"oi-{uuid.uuid4().hex[:8]}",
                text=o.text,
                type=o.type,
                raised_at=datetime.now(),
                proposed_owner=o.proposed_owner,
            )
        )
        event_log.append("propose", kind="open_item", text=o.text)


def propose_quality_rule(
    state: SessionState,
    entity_id: str,
    *,
    description_nl: str,
    baseline_result: str,
    proposed_threshold: str | None,
    ref: str,
    confidence: ProvenanceConfidence,
    event_log: EventLog,
) -> str:
    """Materializes an analyst-measured baseline as a candidate QualityRule
    (status="proposed") — the analyst's finding never writes "confirmed" itself,
    same invariant as apply_lead_proposals. Returns the new rule's id."""
    entity = state.entities[entity_id]
    rule_id = f"qr-{uuid.uuid4().hex[:8]}"
    entity.quality_rules.append(
        QualityRule(
            id=rule_id,
            description_nl=description_nl,
            baseline_result=baseline_result,
            baseline_measured_at=datetime.now(),
            proposed_threshold=proposed_threshold,
            provenance=Provenance(source="data", ref=ref, confidence=confidence, status="proposed"),
        )
    )
    event_log.append("propose", kind="quality_rule", entity_id=entity_id, ref=rule_id, description=description_nl)
    return rule_id


def confirm_quality_rule(state: SessionState, entity_id: str, rule_id: str, event_log: EventLog) -> None:
    entity = state.entities[entity_id]
    if not _confirm_in_list(entity.quality_rules, rule_id):
        raise ValueError(f"quality rule not found: {rule_id}")
    event_log.append("confirm", kind="quality_rule", entity_id=entity_id, ref=rule_id)
    _snapshot(state)


def reject_quality_rule(state: SessionState, entity_id: str, rule_id: str, reason: str, event_log: EventLog) -> None:
    entity = state.entities[entity_id]
    if not _reject_in_list(entity.quality_rules, rule_id, reason):
        raise ValueError(f"quality rule not found: {rule_id}")
    event_log.append("reject", kind="quality_rule", entity_id=entity_id, ref=rule_id, reason=reason)
    _snapshot(state)


def compute_coverage(state: SessionState) -> float:
    """Rough template-coverage heuristic for the UI header (% of template sections
    that have at least one confirmed element)."""
    sections = [
        any(s.provenance.status == "confirmed" for s in state.domain_card.scope_in),
        any(s.provenance.status == "confirmed" for s in state.domain_card.scope_out),
        any(e.provenance.status == "confirmed" for e in state.entities.values()),
        any(
            a.provenance.status == "confirmed"
            for e in state.entities.values()
            for a in e.attributes
        ),
        any(
            s.provenance.status == "confirmed"
            for e in state.entities.values()
            for s in e.lifecycle
        ),
        any(d.provenance.status == "confirmed" for d in state.domain_card.decisions),
        any(
            q.provenance.status == "confirmed"
            for e in state.entities.values()
            for q in e.quality_rules
        ),
    ]
    return sum(sections) / len(sections)
