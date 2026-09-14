from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from src.models.decision import Decision
from src.models.open_item import OpenItem

# TODO(mvp): spec section 4 doesn't define DomainCard.status values separately from
# Provenance.status; reusing the same set until the session flow shows a need to diverge.
DomainCardStatus = Literal["draft", "proposed", "confirmed", "rejected"]


class EntityRef(BaseModel):
    """Lightweight pointer from a DomainCard to a full Entity file in the vault."""

    id: str
    name: str
    status: DomainCardStatus = "draft"


class DomainCard(BaseModel):
    id: str
    name: str
    steward: str
    status: DomainCardStatus = "draft"
    scope_in: list[str] = []
    scope_out: list[str] = []
    source_systems: list[str] = []
    entities: list[EntityRef] = []
    decisions: list[Decision] = []
    open_items: list[OpenItem] = []
