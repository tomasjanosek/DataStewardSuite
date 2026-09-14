from __future__ import annotations

from crewai import LLM, Agent, Crew, Process, Task

from src.agents.prompt_loader import load_prompt
from src.models.strawman import DomainExpertFindings
from src.orchestration.formatting import format_documents
from src.orchestration.json_output import json_schema_instruction, parse_json_output
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
            "Výhradně jeden syrový JSON objekt. Žádný text před ani po JSON, žádné "
            "markdown ``` bloky, žádné \"Thought:\" ani jiný komentář — odpověď MUSÍ "
            "začínat znakem '{' a končit odpovídajícím '}'.\n\n"
            + json_schema_instruction(DomainExpertFindings)
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff(
        inputs={
            "domain_name": domain_name,
            "domain_goal": domain_goal,
            "documents": format_documents(documents),
        }
    )
    return parse_json_output(result.raw, DomainExpertFindings)
