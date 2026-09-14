from __future__ import annotations

from crewai import LLM, Agent, Crew, Process, Task

from src.agents.prompt_loader import load_prompt
from src.models.physical_model import PhysicalModelSlice
from src.models.strawman import ArchitectProposal
from src.orchestration.formatting import format_physical_model_slice


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
            "Strukturovaný návrh (ArchitectProposal): 2 varianty modelu, každá s "
            "entitami (název, grain, fyzické mapování, zdůvodnění se source/ref/"
            "confidence) a s popisem důsledků; plus seznam otázek pro stewarda."
        ),
        agent=agent,
        output_pydantic=ArchitectProposal,
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff(
        inputs={
            "domain_name": domain_name,
            "domain_goal": domain_goal,
            "physical_model_slice": format_physical_model_slice(model_slice),
        }
    )
    if not isinstance(result.pydantic, ArchitectProposal):
        raise RuntimeError(f"architect crew did not return a structured ArchitectProposal: {result.raw!r}")
    return result.pydantic
