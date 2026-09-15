from __future__ import annotations

from crewai import LLM, Agent, Crew, Process, Task

from src.agents.prompt_loader import load_prompt
from src.models.analyst import AnalystFinding, AnalystQueryProposal
from src.models.data_query import QueryResult
from src.models.profile import DataProfile
from src.orchestration.formatting import format_data_profile, format_query_result
from src.orchestration.json_output import json_schema_instruction, parse_json_output


def _agent(llm: LLM) -> Agent:
    return Agent(
        role="Analytik",
        goal="Ověřit nebo vyvrátit hypotézu o datech a kvantifikovat výsledek.",
        backstory=load_prompt("analyst_role.md"),
        llm=llm,
        allow_code_execution=False,
        allow_delegation=False,
        verbose=False,
    )


def propose_query(hypothesis: str, profile: DataProfile, llm: LLM) -> AnalystQueryProposal:
    agent = _agent(llm)
    task = Task(
        description=load_prompt("analyst_query_task.md"),
        expected_output=(
            "Výhradně jeden syrový JSON objekt. Žádný text před ani po JSON, žádné "
            "markdown ``` bloky, žádné \"Thought:\" ani jiný komentář — odpověď MUSÍ "
            "začínat znakem '{' a končit odpovídajícím '}'.\n\n" + json_schema_instruction(AnalystQueryProposal)
        ),
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff(inputs={"hypothesis": hypothesis, "tables_summary": format_data_profile(profile)})
    return parse_json_output(result.raw, AnalystQueryProposal)


def interpret_result(hypothesis: str, query_description: str, result: QueryResult, llm: LLM) -> AnalystFinding:
    agent = _agent(llm)
    task = Task(
        description=load_prompt("analyst_interpret_task.md"),
        expected_output=(
            "Výhradně jeden syrový JSON objekt. Žádný text před ani po JSON, žádné "
            "markdown ``` bloky, žádné \"Thought:\" ani jiný komentář — odpověď MUSÍ "
            "začínat znakem '{' a končit odpovídajícím '}'.\n\n" + json_schema_instruction(AnalystFinding)
        ),
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    crew_result = crew.kickoff(
        inputs={
            "hypothesis": hypothesis,
            "query_description": query_description,
            "result_summary": format_query_result(result),
        }
    )
    return parse_json_output(crew_result.raw, AnalystFinding)
