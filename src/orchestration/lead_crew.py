from __future__ import annotations

from crewai import LLM, Agent, Crew, Process, Task

from src.agents.prompt_loader import load_prompt
from src.models.lead_turn import LeadTurnResult
from src.models.session import SessionState
from src.orchestration.formatting import format_conversation, format_template_state
from src.orchestration.json_output import json_schema_instruction, parse_json_output
from src.tools.domain_config import DomainConfig


def run_lead_turn(state: SessionState, config: DomainConfig, latest_message: str, llm: LLM) -> LeadTurnResult:
    agent = Agent(
        role="Lead",
        goal="Vést stewarda seancí, tlačit na úplnost šablony a doložitelnost, ne na souhlas.",
        backstory=load_prompt("lead_role.md"),
        llm=llm,
        allow_code_execution=False,
        allow_delegation=False,
        verbose=False,
    )

    task = Task(
        description=load_prompt("lead_task.md"),
        expected_output=(
            "Výhradně jeden syrový JSON objekt. Žádný text před ani po JSON, žádné "
            "markdown ``` bloky, žádné \"Thought:\" ani jiný komentář — odpověď MUSÍ "
            "začínat znakem '{' a končit odpovídajícím '}'.\n\n" + json_schema_instruction(LeadTurnResult)
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff(
        inputs={
            "domain_name": config.name,
            "domain_goal": config.goal,
            "phase": state.phase.value,
            "template_state": format_template_state(state),
            "conversation_history": format_conversation(state.conversation),
            "latest_message": latest_message,
        }
    )
    return parse_json_output(result.raw, LeadTurnResult)
