from __future__ import annotations

import datetime
import os
from pathlib import Path

import streamlit as st

from src.orchestration.analyst_crew import interpret_result, propose_query
from src.orchestration.llm import build_llm
from src.orchestration.prep import load_strawman, run_prep, write_strawman
from src.orchestration.resume import build_resume_summary
from src.orchestration.session_actions import (
    compute_coverage,
    confirm_attribute,
    confirm_decision,
    confirm_entity,
    confirm_process_step,
    confirm_quality_rule,
    confirm_scope_item,
    propose_quality_rule,
    reject_attribute,
    reject_decision,
    reject_entity,
    reject_process_step,
    reject_quality_rule,
    reject_scope_item,
)
from src.orchestration.session_runtime import grant_consent, load_state, save_state, send_turn, start_new_session
from src.profiling.profile import load_profile
from src.tools.data_source_factory import build_data_source
from src.tools.doc_loader import list_available_documents, sanitize_filename
from src.tools.domain_config import load_domain_config
from src.tools.event_log import EventLog
from src.tools.vault_writer import VaultWriter

st.set_page_config(page_title="Steward Session", layout="wide")

MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB/file — these are short process write-ups, not attachments


def sessions_dir() -> Path:
    return Path(os.environ.get("SESSIONS_DIR", "sessions"))


def vault_path() -> Path:
    return Path(os.environ.get("VAULT_PATH", "./vault"))


def docs_dir() -> Path:
    return Path(os.environ.get("DOCS_DIR", "data/docs"))


def model_path() -> Path:
    return Path(os.environ.get("MODEL_PATH", "data/physical_model.json"))


def list_domains() -> list[str]:
    return sorted(p.stem for p in Path("config/domains").glob("*.yaml"))


def status_badge(status: str) -> str:
    return {"draft": "⚪", "proposed": "🟡", "confirmed": "🟢", "rejected": "🔴"}.get(status, "⚪")


# ---------------------------------------------------------------------------
# Landing page — plain-language walkthrough shown before the steward starts,
# and reachable any time via the sidebar "❓ Jak seance funguje" button.
# ---------------------------------------------------------------------------
def render_landing_page() -> None:
    st.title("Steward Session")
    st.caption("Jak bude seance probíhat")

    st.markdown(
        "Cílem seance je společně s tebou jako datovým stewardem sestavit a potvrdit "
        "popis datové domény — rozsah, entity, atributy, proces vzniku dat a pravidla "
        "kvality. **Nic se do vaultu nezapíše bez tvého výslovného potvrzení.**"
    )

    steps = [
        (
            "1. Příprava (PREP)",
            "Architekt a doménový expert napřed sami projdou fyzický model a případné "
            "podkladové dokumenty a připraví návrh (tzv. strawman) — koncepční varianty "
            "modelu a seznam otázek pro tebe. Tohle proběhne automaticky, bez tvého zásahu.",
        ),
        (
            "2. Výběr varianty (REVIEW)",
            "Uvidíš navržené varianty konceptuálního modelu i otázky, které z přípravy "
            "vzešly. Vybereš tu, která sedí nejlíp — je to jen výchozí bod, v seanci se "
            "dá měnit.",
        ),
        (
            "3. Souhlas se záznamem",
            "Seance se od začátku do konce zaznamenává do auditního logu — každý tah, "
            "potvrzení i zamítnutí. Než začneme, potvrdíš, že s tím souhlasíš.",
        ),
        (
            "4. Rozhovor s lead agentem",
            "Lead ti bude postupně navrhovat rozsah domény, entity, atributy, proces "
            "vzniku dat a pravidla kvality — na základě přípravy i toho, co mu v chatu "
            "napíšeš. Každou položku vidíš zvlášť a u každé se rozhodneš: ✅ potvrdit, "
            "nebo ❌ zamítnout (se stručným důvodem). Nic se nepotvrdí samo — potvrzuje "
            "jen tvé kliknutí.",
        ),
        (
            "5. Ověření hypotézy (analytik)",
            "Kdykoliv během seance můžeš zadat hypotézu o datech (např. „aktivní měřicí "
            "místo musí mít vždy přiřazené zařízení“). Analytik navrhne strukturovaný "
            "dotaz, ty ho schválíš, spustí se nad reálnými daty a analytik ti nález "
            "interpretuje. Výsledek pak můžeš uložit jako pravidlo kvality k entitě.",
        ),
        (
            "6. Pozastavení a návrat",
            "Seanci lze kdykoliv pozastavit (⏸) a vrátit se k ní později — při návratu "
            "dostaneš krátké shrnutí toho, kde jste skončili.",
        ),
        (
            "7. Dokončení a uložení",
            "Až budeš s popisem domény spokojený/á, kliknutím na „✅ Dokončit a uložit“ "
            "se potvrzený popis deterministicky vyrenderuje do markdown souborů a "
            "commitne do vaultu (git).",
        ),
    ]
    for title, body in steps:
        st.markdown(f"**{title}**")
        st.write(body)

    st.divider()
    st.caption("Stavové ikony u jednotlivých položek: ⚪ návrh · 🟡 navrženo k potvrzení · 🟢 potvrzeno · 🔴 zamítnuto")

    if st.button("Pokračovat k seanci →", type="primary"):
        st.session_state["landing_dismissed"] = True
        st.rerun()


# ---------------------------------------------------------------------------
# REVIEW gate — spec section 6: mandatory gate between PREP and SESSION.
# ---------------------------------------------------------------------------
def render_prep_setup(domain: str, session_id: str) -> None:
    """No strawman yet — let the steward upload background documents and trigger
    PREP directly, instead of needing CLI/SSM access to the server's filesystem."""
    st.warning(f"Pro session_id `{session_id}` zatím neexistuje strawman.")

    if not model_path().exists():
        st.error(
            f"Chybí fyzický model `{model_path()}`. Ten musí na server umístit operátor "
            "předem — je velký a může obsahovat citlivá interní data, proto se nenahrává přes UI."
        )
        return

    docs_path = docs_dir()
    docs_path.mkdir(parents=True, exist_ok=True)

    st.subheader("Podkladové dokumenty")
    existing = list_available_documents(docs_path)
    if existing:
        st.write("Už nahráno:")
        for name in existing:
            st.markdown(f"- {name}")
    else:
        st.caption("Zatím žádné podkladové dokumenty — PREP může běžet i bez nich (výstup pak jen z fyzického modelu).")

    uploaded_files = st.file_uploader(
        "Nahraj podkladové dokumenty (procesní popisy, metodiky, zápisy...)",
        type=["md", "txt"],
        accept_multiple_files=True,
        key=f"doc-upload-{session_id}",
    )
    if uploaded_files:
        saved, skipped = [], []
        for f in uploaded_files:
            if f.size > MAX_UPLOAD_BYTES:
                skipped.append(f.name)
                continue
            safe_name = sanitize_filename(f.name)
            (docs_path / safe_name).write_bytes(f.getvalue())
            saved.append(safe_name)
        if saved:
            st.success(f"Uloženo: {', '.join(saved)}")
        if skipped:
            st.error(f"Přeskočeno (nad {MAX_UPLOAD_BYTES // 1024 // 1024} MB): {', '.join(skipped)}")
        if saved:
            st.rerun()

    if st.button("▶ Spustit PREP", type="primary"):
        config = load_domain_config(f"config/domains/{domain}.yaml")
        with st.spinner("Architekt a doménový expert analyzují model a podklady (obvykle 1–3 min)..."):
            strawman_result = run_prep(
                config, model_path(), docs_path, document_filenames=list_available_documents(docs_path)
            )
            write_strawman(strawman_result, sessions_dir(), session_id)
        st.success(f"Strawman vygenerován — {len(strawman_result.all_questions)} otázek pro stewarda.")
        st.rerun()


def render_review_gate(domain: str, session_id: str) -> None:
    st.header(f"REVIEW: {domain}")
    try:
        strawman = load_strawman(sessions_dir(), session_id)
    except FileNotFoundError:
        render_prep_setup(domain, session_id)
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

            if entity.quality_rules:
                st.markdown("**Pravidla kvality**")
                for q in entity.quality_rules:
                    cols = st.columns([6, 1, 1])
                    baseline = f" — baseline: {q.baseline_result}" if q.baseline_result else ""
                    threshold = f" (navržený práh: {q.proposed_threshold})" if q.proposed_threshold else ""
                    cols[0].markdown(f"{status_badge(q.provenance.status)} {q.description_nl}{baseline}{threshold}")
                    if q.provenance.status not in ("confirmed", "rejected"):
                        if cols[1].button("✅", key=f"confirm-qr-{q.id}"):
                            confirm_quality_rule(state, entity_id, q.id, event_log)
                            save_state(sessions_dir(), session_id, state)
                            st.rerun()
                        reason = cols[2].text_input("důvod", key=f"reason-qr-{q.id}", label_visibility="collapsed", placeholder="důvod")
                        if cols[2].button("❌", key=f"reject-qr-{q.id}") and reason:
                            reject_quality_rule(state, entity_id, q.id, reason, event_log)
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


# ---------------------------------------------------------------------------
# Analyst — spec section 6 phases 5/6: hypothesis checks against data, always
# shown to the steward and approved before running (spec section 7).
# ---------------------------------------------------------------------------
def render_analyst_panel(state, config, session_id: str) -> None:
    st.subheader("Ověření hypotézy (analytik)")

    profile_path = Path("data/profiles") / f"{config.domain}.json"
    if not profile_path.exists():
        st.warning(
            f"Chybí profil dat. Spusť napřed:\n\n"
            f"```\npython -m src.profiling.profile --domain {config.domain}\n```"
        )
        return
    profile = load_profile(profile_path)
    data_source = build_data_source()
    event_log = EventLog(sessions_dir(), session_id)

    wizard_key = f"analyst-{session_id}"
    wizard = st.session_state.setdefault(wizard_key, {"step": "input"})

    hypothesis = st.text_area(
        "Hypotéza", value=wizard.get("hypothesis", ""), placeholder="Např.: Aktivní měřicí místo musí mít vždy přiřazené zařízení."
    )

    if st.button("Navrhnout dotaz", disabled=not hypothesis.strip()):
        with st.spinner("Analytik navrhuje dotaz..."):
            try:
                llm = build_llm()
                proposal = propose_query(hypothesis, profile, llm)
            except Exception as e:  # noqa: BLE001 — LLM output can occasionally fail validation; don't crash the page
                st.error(f"Analytik se nepodařilo strukturovat dotaz, zkus to prosím znovu: {e}")
                st.stop()
        st.session_state[wizard_key] = {"step": "proposed", "hypothesis": hypothesis, "proposal": proposal}
        st.rerun()

    if wizard["step"] in ("proposed", "executed", "interpreted"):
        proposal = wizard["proposal"]
        st.markdown(f"**Zdůvodnění analytika:** {proposal.rationale or proposal.query.description}")
        try:
            preview = data_source.preview_query(proposal.query)
        except Exception as e:  # noqa: BLE001 — surfaced to the steward, not swallowed
            st.error(f"Dotaz nelze spustit: {e}")
            return
        st.code(preview)

    if wizard["step"] == "proposed":
        if st.button("✅ Schválit a spustit dotaz", type="primary"):
            result = data_source.run_query(wizard["proposal"].query)
            event_log.append(
                "data_query", hypothesis=wizard["hypothesis"], preview=preview, row_count=result.row_count
            )
            wizard["step"] = "executed"
            wizard["result"] = result
            st.rerun()

    if wizard["step"] in ("executed", "interpreted"):
        result = wizard["result"]
        st.dataframe([dict(zip(result.columns, row)) for row in result.rows])
        st.caption(f"Celkem řádků: {result.row_count}{' (oříznuto)' if result.truncated else ''}")

    if wizard["step"] == "executed":
        if st.button("Interpretovat nález"):
            with st.spinner("Analytik interpretuje výsledek..."):
                try:
                    llm = build_llm()
                    finding = interpret_result(wizard["hypothesis"], preview, wizard["result"], llm)
                except Exception as e:  # noqa: BLE001 — see propose_query's handler above
                    st.error(f"Analytikovi se nepodařilo interpretovat výsledek, zkus to prosím znovu: {e}")
                    st.stop()
            event_log.append("data_query_result", hypothesis=wizard["hypothesis"], finding=finding.text)
            wizard["step"] = "interpreted"
            wizard["finding"] = finding
            st.rerun()

    if wizard["step"] == "interpreted":
        finding = wizard["finding"]
        st.markdown(f"**Nález analytika:** {finding.text}")
        st.markdown(f"**Kvantifikace:** {finding.quantification}")
        if finding.confirms_hypothesis is not None:
            st.markdown(f"**Potvrzuje hypotézu:** {'ano' if finding.confirms_hypothesis else 'ne'}")

        if state.entities:
            entity_id = st.selectbox(
                "Přidat jako pravidlo kvality k entitě",
                options=list(state.entities.keys()),
                format_func=lambda k: state.entities[k].name,
                key=f"qr-entity-{session_id}",
            )
            if st.button("💾 Uložit jako pravidlo kvality"):
                propose_quality_rule(
                    state, entity_id,
                    description_nl=wizard["hypothesis"],
                    baseline_result=finding.quantification,
                    proposed_threshold=finding.suggested_threshold,
                    ref=f"session:{session_id}",
                    confidence=finding.confidence,
                    event_log=event_log,
                )
                save_state(sessions_dir(), session_id, state)
                st.session_state[wizard_key] = {"step": "input"}
                st.success("Pravidlo kvality navrženo — potvrď ho v panelu entity.")
                st.rerun()

    if wizard["step"] != "input" and st.button("↺ Nová hypotéza"):
        st.session_state[wizard_key] = {"step": "input"}
        st.rerun()


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

    st.divider()
    render_analyst_panel(state, config, session_id)


# ---------------------------------------------------------------------------
def main() -> None:
    st.sidebar.title("Steward Session")
    if st.sidebar.button("❓ Jak seance funguje"):
        st.session_state["landing_dismissed"] = False
        st.rerun()

    if not st.session_state.get("landing_dismissed"):
        render_landing_page()
        return

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
