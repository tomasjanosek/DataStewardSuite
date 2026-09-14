from __future__ import annotations

from crewai import LLM, Agent, Crew, Process, Task

from src.agents.prompt_loader import load_prompt
from src.models.strawman import DomainExpertFindings
from src.orchestration.formatting import format_documents
from src.tools.doc_loader import SourceDocument


def run_domain_expert(
    documents: list[SourceDocument], domain_name: str, domain_goal: str, llm: LLM
) -> DomainExpertFindings:
    agent = Agent(
        role="Doménový expert",
        goal="Najít v podkladech kandidáty na pojmy, procesní kroky a pravidla, a zformulovat otázky.",
        backstory=load_prompt("domain_expert_role.md"),
        llm=llm,
        allow_code_execution=False,
        allow_delegation=False,
        verbose=False,
    )

    task = Task(
        description=load_prompt("domain_expert_task.md"),
        expected_output=(
            "Strukturovaný výstup (DomainExpertFindings): kandidátní pojmy, procesní "
            "kroky (seřazené), metodická pravidla a otázky pro stewarda — každé "
            "tvrzení se source=\"document\", ref na soubor a confidence. Prázdné "
            "seznamy tam, kde podklady mlčí."
        ),
        agent=agent,
        output_pydantic=DomainExpertFindings,
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff(
        inputs={
            "domain_name": domain_name,
            "domain_goal": domain_goal,
            "documents": format_documents(documents),
        }
    )
    if not isinstance(result.pydantic, DomainExpertFindings):
        raise RuntimeError(f"domain_expert crew did not return structured DomainExpertFindings: {result.raw!r}")
    return result.pydantic
