from __future__ import annotations

from src.orchestration.domain_expert_crew import run_domain_expert

from .conftest import requires_llm


@requires_llm
def test_run_domain_expert_returns_structured_findings_with_provenance(tiny_documents, live_llm):
    findings = run_domain_expert(tiny_documents, "Měření", "Popsat proces vzniku dat o měření.", live_llm)

    assert len(findings.candidate_process_steps) >= 1
    for step in findings.candidate_process_steps:
        assert step.source == "document"
        assert step.ref.startswith("meas-proces-popis.md")
        assert step.confidence in ("low", "medium", "high")
    for term in findings.candidate_terms:
        assert term.business_definition.source == "document"
    for rule in findings.candidate_rules:
        assert rule.source == "document"
    for question in findings.questions:
        assert question.raised_by == "domain_expert"
