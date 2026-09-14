from __future__ import annotations

from src.models.physical_model import PhysicalModelSlice
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
