from __future__ import annotations

from crewai import LLM, Agent, Crew, Process, Task

from src.agents.prompt_loader import load_prompt
from src.models.physical_model import PhysicalModelSlice
from src.models.strawman import ArchitectProposal
from src.orchestration.formatting import format_physical_model_slice
from src.orchestration.json_output import json_schema_instruction, parse_json_output


def run_architect(model_slice: PhysicalModelSlice, domain_name: str, domain_goal: str, llm: LLM) -> ArchitectProposal:
    agent = Agent(
        role="Architekt",
        goal="Navrhnout konceptuální model domény ve dvou variantách abstrakce s důsledky.",
        backstory=load_prompt("architect_role.md"),
        llm=llm,
        allow_code_execution=False,
        allow_delegation=False,
        verbose=False,
    )

    task = Task(
        description=load_prompt("architect_task.md"),
        expected_output=(
            "Výhradně jeden syrový JSON objekt. Žádný text před ani po JSON, žádné "
            "markdown ``` bloky, žádné \"Thought:\" ani jiný komentář — odpověď MUSÍ "
            "začínat znakem '{' a končit odpovídajícím '}'.\n\n"
            + json_schema_instruction(ArchitectProposal)
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff(
        inputs={
            "domain_name": domain_name,
            "domain_goal": domain_goal,
            "physical_model_slice": format_physical_model_slice(model_slice),
        }
    )
    return parse_json_output(result.raw, ArchitectProposal)
