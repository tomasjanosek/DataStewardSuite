from __future__ import annotations

from src.models.strawman import Question, Strawman
from src.render.markdown_utils import EMPTY_MARK


def _render_question(q: Question) -> str:
    return f"- ({q.raised_by}, {q.confidence}) {q.text} [zdroj: {q.source}:{q.ref}]"


def render_strawman(strawman: Strawman) -> str:
    """Deterministically renders a Strawman to markdown for the REVIEW gate.

    This is a working document (sessions/{session_id}/strawman.md), not a vault
    artifact — nothing here is confirmed until the steward says so in the session.
    """
    lines: list[str] = [f"# Strawman: {strawman.domain}", "", "*Návrh k revizi před seancí. Nic zde není potvrzeno.*", ""]

    lines += ["## Návrh konceptuálního modelu", ""]
    if not strawman.architect_proposal.variants:
        lines.append(EMPTY_MARK)
    for variant in strawman.architect_proposal.variants:
        lines += [f"### {variant.label}", "", variant.description, ""]
        if variant.entities:
            lines.append("| Entita | Grain | Fyzické mapování | Zdůvodnění |")
            lines.append("|---|---|---|---|")
            for entity in variant.entities:
                mapping = ", ".join(entity.physical_mapping) or "—"
                rationale = entity.rationale
                lines.append(
                    f"| {entity.name} | {entity.grain} | {mapping} | "
                    f"{rationale.text} ({rationale.source}:{rationale.ref}, {rationale.confidence}) |"
                )
        else:
            lines.append(EMPTY_MARK)
        lines += ["", f"**Důsledky:** {variant.consequences}", ""]

    lines += ["## Kandidátní pojmy", ""]
    terms = strawman.domain_expert_findings.candidate_terms
    if not terms:
        lines.append(EMPTY_MARK)
    for term in terms:
        d = term.business_definition
        lines.append(f"- **{term.name}**: {d.text} ({d.source}:{d.ref}, {d.confidence})")

    lines += ["", "## Kandidátní proces vzniku dat", ""]
    steps = sorted(strawman.domain_expert_findings.candidate_process_steps, key=lambda s: s.order)
    if not steps:
        lines.append(EMPTY_MARK)
    for step in steps:
        lines.append(
            f"{step.order}. **{step.actor}** v systému **{step.system}** — "
            f"{step.trigger}: {step.action} ({step.source}:{step.ref}, {step.confidence})"
        )

    lines += ["", "## Kandidátní pravidla", ""]
    rules = strawman.domain_expert_findings.candidate_rules
    if not rules:
        lines.append(EMPTY_MARK)
    for rule in rules:
        lines.append(f"- {rule.text} ({rule.source}:{rule.ref}, {rule.confidence})")

    all_questions = strawman.all_questions
    lines += ["", f"## Otázky pro stewarda ({len(all_questions)})", ""]
    if not all_questions:
        lines.append(EMPTY_MARK)
    for q in all_questions:
        lines.append(_render_question(q))

    lines.append("")
    return "\n".join(lines)
