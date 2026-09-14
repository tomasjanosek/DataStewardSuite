from __future__ import annotations

from pathlib import Path

from src.models.strawman import Strawman
from src.orchestration.architect_crew import run_architect
from src.orchestration.domain_expert_crew import run_domain_expert
from src.orchestration.llm import build_llm
from src.render.strawman_renderer import render_strawman
from src.tools.doc_loader import load_documents
from src.tools.domain_config import DomainConfig
from src.tools.model_loader import load_domain_slice


def run_prep(config: DomainConfig, model_path: Path | str, docs_dir: Path | str) -> Strawman:
    """PREP phase (spec section 6): batch, no human — architect + domain_expert run,
    lead's part (assembling the strawman + question plan) is the caller's job."""
    model_slice = load_domain_slice(
        model_path,
        domain=config.domain,
        folders=config.model_scope.folders,
        table_code_patterns=config.model_scope.table_code_patterns,
    )
    documents = load_documents(docs_dir, config.documents)

    # TODO(mvp): architect's output scales with the candidate slice size (one
    # ArchitectProposal covering every table across 2 variants) — give it a much
    # larger output budget than a normal single-answer task.
    architect_proposal = run_architect(model_slice, config.name, config.goal, build_llm(max_tokens=32000))
    domain_expert_findings = run_domain_expert(documents, config.name, config.goal, build_llm())

    return Strawman(
        domain=config.domain,
        architect_proposal=architect_proposal,
        domain_expert_findings=domain_expert_findings,
    )


def write_strawman(strawman: Strawman, sessions_dir: Path | str, session_id: str) -> Path:
    path = Path(sessions_dir) / session_id / "strawman.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_strawman(strawman), encoding="utf-8")
    return path


if __name__ == "__main__":
    import argparse
    import datetime

    from src.tools.domain_config import load_domain_config

    parser = argparse.ArgumentParser(description="Run the PREP pipeline for a domain.")
    parser.add_argument("--domain", required=True, help="e.g. meas")
    parser.add_argument("--model-path", default="data/physical_model.json")
    parser.add_argument("--docs-dir", default="data/docs")
    parser.add_argument("--sessions-dir", default="sessions")
    parser.add_argument("--session-id", default=None)
    args = parser.parse_args()

    domain_config = load_domain_config(f"config/domains/{args.domain}.yaml")
    session_id = args.session_id or f"{datetime.date.today().isoformat()}-{args.domain}"

    strawman_result = run_prep(domain_config, args.model_path, args.docs_dir)
    output_path = write_strawman(strawman_result, args.sessions_dir, session_id)
    print(f"Strawman written to {output_path}")
    print(f"Questions for steward: {len(strawman_result.all_questions)}")
