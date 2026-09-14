from __future__ import annotations

from src.orchestration.architect_crew import run_architect

from .conftest import requires_llm


@requires_llm
def test_run_architect_returns_structured_proposal_with_provenance(tiny_model_slice, live_llm):
    proposal = run_architect(tiny_model_slice, "Měření", "Popsat proces vzniku dat o měření.", live_llm)

    assert len(proposal.variants) >= 1
    for variant in proposal.variants:
        assert variant.label
        assert variant.consequences
        for entity in variant.entities:
            assert entity.name
            assert entity.rationale.source == "physical_model"
            assert entity.rationale.ref
            assert entity.rationale.confidence in ("low", "medium", "high")
    for question in proposal.questions:
        assert question.raised_by == "architect"
        assert question.ref
