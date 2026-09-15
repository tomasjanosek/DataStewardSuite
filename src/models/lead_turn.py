from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from src.models.provenance import ProvenanceConfidence

# Proposals below only ever come from the live conversation — source is always
# "steward" (the steward said it directly) or "inference" (the lead inferred it from
# what was said), never "physical_model"/"document"/"data".
ConversationSource = Literal["steward", "inference"]


class ProposedAttribute(BaseModel):
    entity_id: str
    name: str
    business_meaning: str
    physical_column: str
    mandatory: bool
    source_of_truth: str
    source: ConversationSource
    ref: str
    confidence: ProvenanceConfidence


class ProposedProcessStep(BaseModel):
    entity_id: str
    order: int
    actor: str
    system: str
    trigger: str
    action: str
    source: ConversationSource
    ref: str
    confidence: ProvenanceConfidence


class ProposedDecision(BaseModel):
    text: str
    source: ConversationSource
    ref: str
    confidence: ProvenanceConfidence


class ProposedOpenItem(BaseModel):
    text: str
    type: Literal["decision_needed", "owner_missing", "conflict", "data_issue"]
    proposed_owner: str | None = None


class LeadTurnResult(BaseModel):
    """One turn of the lead's conversation, structured per spec section 5: the lead
    proposes at most (never confirms) — proposals get materialized with
    provenance.status="proposed" and only a steward's explicit confirm/reject action
    (never the LLM) can move them further. See src/orchestration/session_actions.py.
    """

    reply: str
    proposed_attributes: list[ProposedAttribute] = []
    proposed_process_steps: list[ProposedProcessStep] = []
    proposed_decisions: list[ProposedDecision] = []
    proposed_open_items: list[ProposedOpenItem] = []
