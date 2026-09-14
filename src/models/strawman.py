from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from src.models.provenance import ProvenanceConfidence, ProvenanceSource


class SourcedClaim(BaseModel):
    """A pre-session proposal. Not a governed artifact claim yet — no status/
    confirmed_at, since only the steward's live confirmation can produce one of
    those (see Provenance). The lead folds confirmed pieces of a Strawman into real
    artifact claims during the session.
    """

    text: str
    source: ProvenanceSource
    ref: str
    confidence: ProvenanceConfidence


class Question(BaseModel):
    text: str
    raised_by: Literal["architect", "domain_expert"]
    source: ProvenanceSource
    ref: str
    confidence: ProvenanceConfidence


class ConceptualEntityProposal(BaseModel):
    name: str
    grain: str
    physical_mapping: list[str] = []
    rationale: SourcedClaim


class ModelVariant(BaseModel):
    label: str
    description: str
    entities: list[ConceptualEntityProposal] = []
    consequences: str


class ArchitectProposal(BaseModel):
    # TODO(mvp): spec asks for exactly 2 variants; not hard-enforced here (LLM output
    # validation on a strict length is brittle) — the task prompt asks for 2 and the
    # REVIEW gate is where a mismatch would actually get caught.
    variants: list[ModelVariant] = []
    questions: list[Question] = []


class DomainTermProposal(BaseModel):
    name: str
    business_definition: SourcedClaim


class ProcessStepProposal(BaseModel):
    order: int
    actor: str
    system: str
    trigger: str
    action: str
    source: ProvenanceSource
    ref: str
    confidence: ProvenanceConfidence


class DomainExpertFindings(BaseModel):
    candidate_terms: list[DomainTermProposal] = []
    candidate_process_steps: list[ProcessStepProposal] = []
    candidate_rules: list[SourcedClaim] = []
    questions: list[Question] = []


class Strawman(BaseModel):
    domain: str
    architect_proposal: ArchitectProposal
    domain_expert_findings: DomainExpertFindings

    @property
    def all_questions(self) -> list[Question]:
        return [*self.architect_proposal.questions, *self.domain_expert_findings.questions]
