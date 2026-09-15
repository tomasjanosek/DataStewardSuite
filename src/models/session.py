from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from src.models.domain_card import DomainCard
from src.models.entity import Entity


class SessionPhase(str, Enum):
    """Spec section 6, [SESSION] phases 1-7. Phases can be skipped and revisited —
    this enum only tracks "where we currently are", not a strict sequence."""

    CONSENT = "consent"
    SCOPE = "scope"
    ENTITIES = "entities"
    PROCESS = "process"
    DATA = "data"  # TODO(mvp, milestone 4): needs the analyst/Redshift tool.
    QUALITY = "quality"  # TODO(mvp, milestone 4): needs baseline measurement.
    DECISIONS = "decisions"
    FINALIZED = "finalized"


class ChatMessage(BaseModel):
    role: Literal["steward", "lead"]
    text: str
    at: datetime


class SessionState(BaseModel):
    """CrewAI Flow state. Needs an `id` field — the flow persistence layer keys on it.

    Materialized to sessions/{id}/state.json by JsonFileFlowPersistence; every turn,
    confirmation and rejection is additionally appended to sessions/{id}/events.jsonl
    (the source of truth — state.json is a derived snapshot, per spec section 7).
    """

    id: str
    domain: str
    phase: SessionPhase = SessionPhase.CONSENT
    consent_given: bool = False
    paused: bool = False
    domain_card: DomainCard
    entities: dict[str, Entity] = {}
    conversation: list[ChatMessage] = []
    # Transient: set via kickoff(inputs={"pending_message": ...}), consumed and
    # cleared by SessionFlow.respond() in the same turn. Never meaningful at rest.
    pending_message: str = ""
    # Snapshot of domain_card+entities as of the last steward confirmation/rejection —
    # compared against current state to build the resume summary (spec section 6:
    # "Po resume lead nesmí pokracovat v pul vety").
    last_confirmed_snapshot: dict | None = None
