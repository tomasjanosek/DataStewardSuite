from __future__ import annotations

from pydantic import BaseModel


class PhysicalColumn(BaseModel):
    """A column as it exists in the catalog export — no claims, no provenance yet."""

    code: str
    name: str
    data_type: str
    mandatory: bool
    business_meaning: str
    stereotype: str | None = None  # e.g. "dw_column", "audit_column", "history_column"


class PhysicalTable(BaseModel):
    code: str
    name: str
    zone: str  # top-level folder, e.g. "CORE ZONE", "DATAMARTS", "LANDING ZONE"
    folder_path: list[str]
    business_meaning: str
    table_kind: str | None = None  # e.g. "dimension", "fact"
    columns: list[PhysicalColumn] = []
    source_tables: list[str] = []  # codes of tables this one is loaded/mapped from


class PhysicalModelSlice(BaseModel):
    """The deterministic candidate slice of the catalog for one domain (PREP phase input)."""

    domain: str
    tables: list[PhysicalTable] = []
