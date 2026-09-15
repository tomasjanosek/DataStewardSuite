from __future__ import annotations

from src.orchestration.session_runtime import grant_consent, load_state, send_turn, start_new_session

from .conftest import requires_llm


@requires_llm
def test_send_turn_persists_conversation_and_survives_a_fresh_flow_instance(
    tmp_path, sample_config, sample_variant, live_llm
):
    start_new_session(tmp_path, "2026-09-15-meas", sample_config, sample_variant)
    grant_consent(tmp_path, "2026-09-15-meas")

    state_after_first = send_turn(
        tmp_path, "2026-09-15-meas", sample_config,
        "Ahoj, měřicí místo zakládá technik při instalaci zařízení v systému AVE.",
        live_llm,
    )

    assert len(state_after_first.conversation) == 2
    assert state_after_first.conversation[0].role == "steward"
    assert state_after_first.conversation[1].role == "lead"
    assert state_after_first.conversation[1].text

    # A brand new SessionFlow instance (as a fresh Streamlit rerun or process would
    # create) must restore this exact state from disk, not start over.
    reloaded = load_state(tmp_path, "2026-09-15-meas")
    assert len(reloaded.conversation) == 2

    state_after_second = send_turn(
        tmp_path, "2026-09-15-meas", sample_config, "Díky, to dává smysl.", live_llm
    )
    assert len(state_after_second.conversation) == 4
    assert state_after_second.conversation[0].text == state_after_first.conversation[0].text
