from __future__ import annotations

import datetime
import os
from pathlib import Path

import streamlit as st

from src.orchestration.llm import build_llm
from src.orchestration.prep import load_strawman
from src.orchestration.resume import build_resume_summary
from src.orchestration.session_actions import (
    compute_coverage,
    confirm_attribute,
    confirm_decision,
    confirm_entity,
    confirm_process_step,
    confirm_scope_item,
    reject_attribute,
    reject_decision,
    reject_entity,
    reject_process_step,
    reject_scope_item,
)
from src.orchestration.session_runtime import grant_consent, load_state, save_state, send_turn, start_new_session
from src.tools.domain_config import load_domain_config
from src.tools.event_log import EventLog
from src.tools.vault_writer import VaultWriter

st.set_page_config(page_title="Steward Session", layout="wide")


def sessions_dir() -> Path:
    return Path(os.environ.get("SESSIONS_DIR", "sessions"))


def vault_path() -> Path:
    return Path(os.environ.get("VAULT_PATH", "./vault"))


def list_domains() -> list[str]:
    return sorted(p.stem for p in Path("config/domains").glob("*.yaml"))


def status_badge(status: str) -> str:
    return {"draft": "⚪", "proposed": "🟡", "confirmed": "🟢", "rejected": "🔴"}.get(status, "⚪")


# ---------------------------------------------------------------------------
# REVIEW gate — spec section 6: mandatory gate between PREP and SESSION.
# ---------------------------------------------------------------------------
def render_review_gate(domain: str, session_id: str) -> None:
    st.header(f"REVIEW: {domain}")
    try:
        strawman = load_strawman(sessions_dir(), session_id)
    except FileNotFoundError:
        st.warning(
            f"Pro session_id `{session_id}` neexistuje strawman. Nejdřív spusť PREP:\n\n"
            f"```\npython -m src.orchestration.prep --domain {domain} --session-id {session_id}\n```"
        )
        return

    if not strawman.architect_proposal.variants:
        st.error("Strawman neobsahuje žádnou variantu modelu.")
        return

    st.caption("Vyber variantu konceptuálního modelu, kterou seance použije jako výchozí bod.")
    labels = [v.label for v in strawman.architect_proposal.variants]
    choice = st.radio("Varianta", labels, index=0)
    variant = next(v for v in strawman.architect_proposal.variants if v.label == choice)

    st.markdown(f"**{variant.label}**")
    st.write(variant.description)
    for e in variant.entities:
        st.markdown(f"- **{e.name}** — {e.grain}")
    st.markdown(f"**Důsledky:** {variant.consequences}")

    if strawman.all_questions:
        with st.expander(f"Otázky pro stewarda ({len(strawman.all_questions)})"):
            for q in strawman.all_questions:
                st.markdown(f"- ({q.raised_by}, {q.confidence}) {q.text}")

    if st.button("Zahájit seanci s touto variantou", type="primary"):
        start_new_session(sessions_dir(), session_id, load_domain_config(f"config/domains/{domain}.yaml"), variant)
        st.rerun()


# ---------------------------------------------------------------------------
# Consent gate — spec section 8: first step of the conversation.
# ---------------------------------------------------------------------------
def render_consent_gate(session_id: str) -> None:
    st.header("Souhlas se záznamem")
    st.write(
        "Tato seance se zaznamenává — každý tah, potvrzení a zamítnutí se ukládá "
        "do auditního logu. Pokračováním s tím souhlasíš."
    )
    if st.button("Souhlasím, pokračovat", type="primary"):
        grant_consent(sessions_dir(), session_id)
        st.rerun()


# ---------------------------------------------------------------------------
# SESSION screen
# ---------------------------------------------------------------------------
def render_artifact_panel(state, session_id: str) -> None:
    event_log = EventLog(sessions_dir(), session_id)
    card = state.domain_card

    st.subheader("Rozsah domény")
    for direction, items in (("scope_in", card.scope_in), ("scope_out", card.scope_out)):
        for item in items:
            cols = st.columns([6, 1, 1])
            cols[0].markdown(f"{status_badge(item.provenance.status)} {item.text}")
            if item.provenance.status not in ("confirmed", "rejected"):
                if cols[1].button("✅", key=f"confirm-{direction}-{item.id}"):
                    confirm_scope_item(state, direction, item.id, event_log)
                    save_state(sessions_dir(), session_id, state)
                    st.rerun()
                reason_key = f"reason-{direction}-{item.id}"
                reason = cols[2].text_input("důvod", key=reason_key, label_visibility="collapsed", placeholder="důvod zamítnutí")
                if cols[2].button("❌", key=f"reject-{direction}-{item.id}") and reason:
                    reject_scope_item(state, direction, item.id, reason, event_log)
                    save_state(sessions_dir(), session_id, state)
                    st.rerun()
            elif item.provenance.status == "rejected" and item.provenance.rejection_reason:
                cols[1].caption(item.provenance.rejection_reason)

    st.subheader("Entity")
    for entity_id, entity in state.entities.items():
        with st.expander(f"{status_badge(entity.provenance.status)} {entity.name}", expanded=False):
            st.write(entity.business_definition)
            st.caption(f"Grain: {entity.grain}")
            if entity.provenance.status not in ("confirmed", "rejected"):
                c1, c2, c3 = st.columns([1, 1, 4])
                if c1.button("✅ Potvrdit entitu", key=f"confirm-entity-{entity_id}"):
                    confirm_entity(state, entity_id, event_log)
                    save_state(sessions_dir(), session_id, state)
                    st.rerun()
                reason = c3.text_input("důvod", key=f"reason-entity-{entity_id}", label_visibility="collapsed", placeholder="důvod zamítnutí")
                if c2.button("❌ Zamítnout", key=f"reject-entity-{entity_id}") and reason:
                    reject_entity(state, entity_id, reason, event_log)
                    save_state(sessions_dir(), session_id, state)
                    st.rerun()

            if entity.attributes:
                st.markdown("**Atributy**")
                for a in entity.attributes:
                    cols = st.columns([6, 1, 1])
                    cols[0].markdown(f"{status_badge(a.provenance.status)} **{a.name}**: {a.business_meaning}")
                    if a.provenance.status not in ("confirmed", "rejected"):
                        if cols[1].button("✅", key=f"confirm-attr-{a.id}"):
                            confirm_attribute(state, entity_id, a.id, event_log)
                            save_state(sessions_dir(), session_id, state)
                            st.rerun()
                        reason = cols[2].text_input("důvod", key=f"reason-attr-{a.id}", label_visibility="collapsed", placeholder="důvod")
                        if cols[2].button("❌", key=f"reject-attr-{a.id}") and reason:
                            reject_attribute(state, entity_id, a.id, reason, event_log)
                            save_state(sessions_dir(), session_id, state)
                            st.rerun()

            if entity.lifecycle:
                st.markdown("**Proces vzniku dat**")
                for s in sorted(entity.lifecycle, key=lambda s: s.order):
                    cols = st.columns([6, 1, 1])
                    cols[0].markdown(f"{status_badge(s.provenance.status)} {s.order}. {s.actor} @ {s.system}: {s.action}")
                    if s.provenance.status not in ("confirmed", "rejected"):
                        if cols[1].button("✅", key=f"confirm-step-{s.id}"):
                            confirm_process_step(state, entity_id, s.id, event_log)
                            save_state(sessions_dir(), session_id, state)
                            st.rerun()
                        reason = cols[2].text_input("důvod", key=f"reason-step-{s.id}", label_visibility="collapsed", placeholder="důvod")
                        if cols[2].button("❌", key=f"reject-step-{s.id}") and reason:
                            reject_process_step(state, entity_id, s.id, reason, event_log)
                            save_state(sessions_dir(), session_id, state)
                            st.rerun()

    if card.decisions:
        st.subheader("Rozhodnutí")
        for d in card.decisions:
            cols = st.columns([6, 1, 1])
            cols[0].markdown(f"{status_badge(d.provenance.status)} {d.text}")
            if d.provenance.status not in ("confirmed", "rejected"):
                if cols[1].button("✅", key=f"confirm-dec-{d.id}"):
                    confirm_decision(state, d.id, event_log)
                    save_state(sessions_dir(), session_id, state)
                    st.rerun()
                reason = cols[2].text_input("důvod", key=f"reason-dec-{d.id}", label_visibility="collapsed", placeholder="důvod")
                if cols[2].button("❌", key=f"reject-dec-{d.id}") and reason:
                    reject_decision(state, d.id, reason, event_log)
                    save_state(sessions_dir(), session_id, state)
                    st.rerun()

    if card.open_items:
        st.subheader("Otevřené body")
        for o in card.open_items:
            owner = o.proposed_owner or "*(bez vlastníka)*"
            st.markdown(f"- [{o.status}] ({o.type}) {o.text} — {owner}")


def render_session_screen(state, config, session_id: str) -> None:
    coverage = compute_coverage(state)
    header = st.columns([3, 2, 1, 1])
    header[0].markdown(f"### {config.name}")
    header[1].progress(coverage, text=f"Pokrytí šablony: {coverage:.0%}")
    if header[2].button("⏸ Pozastavit"):
        state.paused = True
        save_state(sessions_dir(), session_id, state)
        st.rerun()
    if header[3].button("✅ Dokončit a uložit"):
        writer = VaultWriter(vault_path())
        writer.write_domain_card(state.domain_card)
        for entity in state.entities.values():
            writer.write_entity(entity)
        writer.commit(session_id, f"Session {session_id}: update {config.name}")
        st.success("Uloženo do vaultu.")

    greeted_key = f"greeted-{session_id}"
    if not st.session_state.get(greeted_key):
        st.info(build_resume_summary(state))
        st.session_state[greeted_key] = True

    left, right = st.columns([3, 2])

    with left:
        for m in state.conversation:
            with st.chat_message("user" if m.role == "steward" else "assistant"):
                st.write(m.text)

        message = st.chat_input("Napiš stewardovi odpověď...")
        if message:
            with st.spinner("Lead přemýšlí..."):
                llm = build_llm()
                new_state = send_turn(sessions_dir(), session_id, config, message, llm)
            st.session_state[greeted_key] = True
            _ = new_state
            st.rerun()

    with right:
        render_artifact_panel(state, session_id)


# ---------------------------------------------------------------------------
def main() -> None:
    st.sidebar.title("Steward Session")
    domains = list_domains()
    if not domains:
        st.error("V config/domains/ nejsou žádné domény.")
        return
    domain = st.sidebar.selectbox("Doména", domains)
    default_session_id = f"{datetime.date.today().isoformat()}-{domain}"
    session_id = st.sidebar.text_input("session_id", value=default_session_id)

    state = load_state(sessions_dir(), session_id)

    if state is None:
        render_review_gate(domain, session_id)
        return

    config = load_domain_config(f"config/domains/{domain}.yaml")

    if not state.consent_given:
        render_consent_gate(session_id)
        return

    if state.paused:
        st.info("Seance je pozastavená.")
        if st.button("▶ Pokračovat"):
            state.paused = False
            save_state(sessions_dir(), session_id, state)
            st.rerun()
        return

    render_session_screen(state, config, session_id)


main()
