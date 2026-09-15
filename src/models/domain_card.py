from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from src.models.decision import Decision
from src.models.open_item import OpenItem
from src.models.provenance import Provenance

# TODO(mvp): spec section 4 doesn't define DomainCard.status values separately from
# Provenance.status; reusing the same set until the session flow shows a need to diverge.
DomainCardStatus = Literal["draft", "proposed", "confirmed", "rejected"]


class EntityRef(BaseModel):
    """Lightweight pointer from a DomainCard to a full Entity file in the vault."""

    id: str
    name: str
    status: DomainCardStatus = "draft"


class ScopeStatement(BaseModel):
    """One scope_in/scope_out claim. Session phase 2 confirms/rejects these one at a
    time — see spec acceptance criteria #2/#3 — so each needs its own id and
    provenance, not just a bare string.
    """

    id: str
    text: str
    provenance: Provenance


class DomainCard(BaseModel):
    id: str
    name: str
    steward: str
    status: DomainCardStatus = "draft"
    scope_in: list[ScopeStatement] = []
    scope_out: list[ScopeStatement] = []
    source_systems: list[str] = []
    entities: list[EntityRef] = []
    decisions: list[Decision] = []
    open_items: list[OpenItem] = []
