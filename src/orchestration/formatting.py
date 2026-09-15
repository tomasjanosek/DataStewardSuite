from __future__ import annotations

from src.models.data_query import QueryResult
from src.models.physical_model import PhysicalModelSlice
from src.models.profile import DataProfile
from src.models.session import ChatMessage, SessionState
from src.tools.doc_loader import SourceDocument


def format_physical_model_slice(model_slice: PhysicalModelSlice) -> str:
    """Compact text rendering of a PhysicalModelSlice for the architect's prompt.

    Deliberately not JSON — keeps token usage down for a ~100+ table slice while
    keeping every fact (code, zone, comment, columns, lineage) machine-checkable
    by the architect against `ref`.
    """
    lines: list[str] = []
    for table in model_slice.tables:
        zone_path = " > ".join(table.folder_path) or table.zone
        lines.append(f"## {table.code} ({table.name}) — {zone_path}")
        if table.table_kind:
            lines.append(f"kind: {table.table_kind}")
        if table.business_meaning:
            lines.append(f"popis: {table.business_meaning}")
        if table.source_tables:
            lines.append(f"plní se z: {', '.join(table.source_tables)}")
        if table.columns:
            lines.append("sloupce:")
            for col in table.columns:
                mand = "povinný" if col.mandatory else "nepovinný"
                meaning = f" — {col.business_meaning}" if col.business_meaning else ""
                lines.append(f"  - {col.code} ({col.data_type}, {mand}){meaning}")
        lines.append("")
    return "\n".join(lines)


def format_documents(documents: list[SourceDocument]) -> str:
    if not documents:
        return "(žádné podkladové dokumenty)"
    parts = []
    for doc in documents:
        parts.append(f"### {doc.filename}\n\n{doc.content}")
    return "\n\n".join(parts)


def format_template_state(state: SessionState) -> str:
    """Compact text rendering of the artifact-in-progress for the lead's prompt."""
    lines: list[str] = []

    lines.append("Rozsah — patří do domény:")
    for s in state.domain_card.scope_in:
        lines.append(f"  - [{s.provenance.status}] (id={s.id}) {s.text}")
    lines.append("Rozsah — nepatří do domény:")
    for s in state.domain_card.scope_out:
        lines.append(f"  - [{s.provenance.status}] (id={s.id}) {s.text}")

    lines.append("")
    lines.append("Entity:")
    for entity in state.entities.values():
        lines.append(f"  - [{entity.provenance.status}] (id={entity.id}) {entity.name}: {entity.business_definition}")
        for a in entity.attributes:
            lines.append(f"      atribut [{a.provenance.status}] (id={a.id}) {a.name}: {a.business_meaning}")
        for step in sorted(entity.lifecycle, key=lambda s: s.order):
            lines.append(
                f"      krok [{step.provenance.status}] (id={step.id}) {step.order}. "
                f"{step.actor} @ {step.system}: {step.action}"
            )

    lines.append("")
    lines.append("Rozhodnutí:")
    for d in state.domain_card.decisions:
        lines.append(f"  - [{d.provenance.status}] (id={d.id}) {d.text}")

    lines.append("")
    lines.append("Otevřené body:")
    for o in state.domain_card.open_items:
        lines.append(f"  - [{o.status}] (id={o.id}) {o.text}")

    return "\n".join(lines)


def format_conversation(messages: list[ChatMessage], limit: int = 20) -> str:
    if not messages:
        return "(zatím žádná konverzace)"
    lines = [f"{m.role}: {m.text}" for m in messages[-limit:]]
    return "\n".join(lines)


def format_data_profile(profile: DataProfile) -> str:
    lines: list[str] = []
    for t in profile.tables:
        lines.append(f"## {t.table} — {t.row_count} řádků")
        for c in t.columns:
            range_txt = f", rozsah {c.min_value}..{c.max_value}" if c.min_value is not None else ""
            lines.append(
                f"  - {c.name}: null {c.null_pct:.1f}% ({c.null_count}), "
                f"distinct {c.distinct_count}{range_txt}"
            )
        lines.append("")
    return "\n".join(lines)


def format_query_result(result: QueryResult) -> str:
    lines = [" | ".join(result.columns)]
    for row in result.rows[:50]:
        lines.append(" | ".join(str(v) for v in row))
    lines.append(f"(celkem řádků: {result.row_count}{', oříznuto' if result.truncated else ''})")
    return "\n".join(lines)
