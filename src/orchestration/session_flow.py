from __future__ import annotations

from datetime import datetime

from crewai import LLM
from crewai.flow.flow import Flow, start
from crewai.flow.persistence import persist

from src.models.session import ChatMessage, SessionState
from src.orchestration.lead_crew import run_lead_turn
from src.orchestration.persistence import SHARED_PERSISTENCE
from src.orchestration.session_actions import apply_lead_proposals
from src.tools.domain_config import DomainConfig
from src.tools.event_log import EventLog


@persist(persistence=SHARED_PERSISTENCE)
class SessionFlow(Flow[SessionState]):
    """One respond() call handles exactly one steward turn (spec section 6: "Lead je
    konverzační smyčka obsluhující jeden tah uživatele"). Each turn is a fresh
    Python-level Flow instance — state is restored from JsonFileFlowPersistence via
    kickoff's `id` input, not kept in memory across calls (matches how a Streamlit
    rerun or a new CLI invocation actually works).

    Class-level @persist() is deliberate here, not an oversight of spec section 7's
    warning against it: that warning is about a *multi-step* Flow saving — and
    potentially restoring mid-step — after every intermediate method. This Flow has
    exactly one flow-registered method, so "persist after every method" and "persist
    at one terminal step" are the same thing. Do not add a second @start()/@listen()
    method to this class without switching to method-level persistence.
    """

    def __init__(
        self,
        *,
        initial_state: SessionState,
        config: DomainConfig,
        llm: LLM,
        event_log: EventLog,
        persistence: object = None,
    ) -> None:
        # `persistence` is injected by the @persist(...) class decorator above
        # (always SHARED_PERSISTENCE) — callers should never pass it explicitly.
        self.initial_state = initial_state
        self._config = config
        self._llm = llm
        self._event_log = event_log
        super().__init__(persistence=persistence or SHARED_PERSISTENCE)

    @start()
    def respond(self) -> str:
        message = self.state.pending_message
        self.state.pending_message = ""
        if not message:
            return ""

        self.state.conversation.append(ChatMessage(role="steward", text=message, at=datetime.now()))
        self._event_log.append("turn", role="steward", text=message)

        turn = run_lead_turn(self.state, self._config, message, self._llm)
        apply_lead_proposals(self.state, turn, self.state.id, self._event_log)

        self.state.conversation.append(ChatMessage(role="lead", text=turn.reply, at=datetime.now()))
        self._event_log.append("turn", role="lead", text=turn.reply)
        return turn.reply
