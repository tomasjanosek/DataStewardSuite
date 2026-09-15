from __future__ import annotations

from pydantic import BaseModel

from src.models.data_query import HypothesisQuery
from src.models.provenance import ProvenanceConfidence


class AnalystQueryProposal(BaseModel):
    query: HypothesisQuery
    rationale: str  # why this query tests the hypothesis — shown alongside the preview


class AnalystFinding(BaseModel):
    """Spec section 5: "Analytik formuluje nalez vzdy jako vlastni nejistotu, ne jako
    pristizeni stewarda" — `text` must read as the analyst's own uncertainty, not an
    accusation. Enforced by the prompt, not by this schema.
    """

    text: str
    confirms_hypothesis: bool | None  # None = inconclusive from this query alone
    quantification: str  # e.g. "12 z 10 482 zaznamu (0.11 %)"
    confidence: ProvenanceConfidence
    suggested_threshold: str | None = None  # candidate QualityRule.proposed_threshold
