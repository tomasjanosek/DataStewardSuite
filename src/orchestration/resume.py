from __future__ import annotations

from src.models.session import SessionState


def _confirmed_scope_lines(items: list) -> list[str]:
    return [f"- {s.text}" for s in items if s.provenance.status == "confirmed"]


def _pending_since_snapshot(state: SessionState) -> list[str]:
    """Proposed items that exist now but weren't in the last confirmation snapshot —
    i.e. what accumulated since the steward last acted, waiting for a decision."""
    snapshot = state.last_confirmed_snapshot or {}
    snap_entities = snapshot.get("entities", {})
    lines: list[str] = []

    for entity_id, entity in state.entities.items():
        snap_entity = snap_entities.get(entity_id, {})
        snap_attr_ids = {a["id"] for a in snap_entity.get("attributes", [])}
        snap_step_ids = {s["id"] for s in snap_entity.get("lifecycle", [])}
        for a in entity.attributes:
            if a.provenance.status == "proposed" and a.id not in snap_attr_ids:
                lines.append(f"- [{entity.name}] atribut **{a.name}**: {a.business_meaning}")
        for s in entity.lifecycle:
            if s.provenance.status == "proposed" and s.id not in snap_step_ids:
                lines.append(f"- [{entity.name}] krok {s.order}: {s.actor} — {s.action}")

    snap_card = snapshot.get("domain_card", {})
    snap_decision_ids = {d["id"] for d in snap_card.get("decisions", [])}
    for d in state.domain_card.decisions:
        if d.provenance.status == "proposed" and d.id not in snap_decision_ids:
            lines.append(f"- rozhodnutí: {d.text}")

    return lines


def build_resume_summary(state: SessionState) -> str:
    """Deterministic resume message: what's confirmed, then what's new/pending since
    the last confirmation. The lead must show this BEFORE continuing the conversation
    (spec section 6) — rendered without an LLM call since correctness here matters
    more than phrasing.
    """
    lines: list[str] = [f"Seance pro doménu **{state.domain_card.name}** byla obnovena.", "", "## Co je zatím potvrzeno"]

    confirmed_in = _confirmed_scope_lines(state.domain_card.scope_in)
    confirmed_out = _confirmed_scope_lines(state.domain_card.scope_out)
    confirmed_entities = [e for e in state.entities.values() if e.provenance.status == "confirmed"]
    confirmed_decisions = [d for d in state.domain_card.decisions if d.provenance.status == "confirmed"]

    if confirmed_in:
        lines += ["", "**Patří do domény:**", *confirmed_in]
    if confirmed_out:
        lines += ["", "**Nepatří do domény:**", *confirmed_out]
    if confirmed_entities:
        lines += ["", "**Entity:**", *[f"- {e.name}" for e in confirmed_entities]]
    if confirmed_decisions:
        lines += ["", "**Rozhodnutí:**", *[f"- {d.text}" for d in confirmed_decisions]]
    if not (confirmed_in or confirmed_out or confirmed_entities or confirmed_decisions):
        lines += ["", "*(zatím nic)*"]

    pending = _pending_since_snapshot(state)
    lines += ["", "## Co čeká na rozhodnutí (nově navrženo od poslední akce)", ""]
    lines += pending if pending else ["*(nic nového)*"]

    return "\n".join(lines)
