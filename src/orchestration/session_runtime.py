from __future__ import annotations

from pathlib import Path

from crewai import LLM

from src.models.session import SessionPhase, SessionState
from src.models.strawman import ModelVariant
from src.orchestration.persistence import SHARED_PERSISTENCE, JsonFileFlowPersistence
from src.orchestration.session_actions import new_session_state
from src.orchestration.session_flow import SessionFlow
from src.tools.domain_config import DomainConfig
from src.tools.event_log import EventLog


def load_state(sessions_dir: Path | str, session_id: str) -> SessionState | None:
    JsonFileFlowPersistence.configure(sessions_dir)
    stored = SHARED_PERSISTENCE.load_state(session_id)
    return SessionState.model_validate(stored) if stored is not None else None


def save_state(sessions_dir: Path | str, session_id: str, state: SessionState) -> None:
    JsonFileFlowPersistence.configure(sessions_dir)
    SHARED_PERSISTENCE.save_state(session_id, "manual_update", state)


def start_new_session(
    sessions_dir: Path | str, session_id: str, config: DomainConfig, variant: ModelVariant
) -> SessionState:
    JsonFileFlowPersistence.configure(sessions_dir)
    SHARED_PERSISTENCE.init_db()
    state = new_session_state(session_id, config, variant)
    SHARED_PERSISTENCE.save_state(session_id, "seed", state)
    EventLog(sessions_dir, session_id).append("session_started", domain=config.domain, variant=variant.label)
    return state


def grant_consent(sessions_dir: Path | str, session_id: str) -> SessionState:
    state = load_state(sessions_dir, session_id)
    if state is None:
        raise ValueError(f"no session found: {session_id}")
    state.consent_given = True
    state.phase = SessionPhase.SCOPE
    save_state(sessions_dir, session_id, state)
    EventLog(sessions_dir, session_id).append("consent_given")
    return state


def send_turn(sessions_dir: Path | str, session_id: str, config: DomainConfig, message: str, llm: LLM) -> SessionState:
    """Runs one steward turn through SessionFlow and returns the updated state
    (already persisted — SessionFlow's class-level @persist() saves it)."""
    JsonFileFlowPersistence.configure(sessions_dir)
    event_log = EventLog(sessions_dir, session_id)
    # Placeholder state to satisfy Flow's construction; kickoff's id-based restore
    # (below) immediately replaces it with the real persisted state.
    placeholder = new_session_state(session_id, config, ModelVariant(label="", description="", consequences=""))

    flow = SessionFlow(initial_state=placeholder, config=config, llm=llm, event_log=event_log)
    flow.kickoff(inputs={"id": session_id, "pending_message": message})
    return flow.state
