from __future__ import annotations

from src.models.session import SessionPhase
from src.orchestration.session_runtime import grant_consent, load_state, save_state, start_new_session


def test_start_new_session_persists_and_reloads(tmp_path, sample_config, sample_variant):
    state = start_new_session(tmp_path, "2026-09-15-meas", sample_config, sample_variant)

    reloaded = load_state(tmp_path, "2026-09-15-meas")
    assert reloaded is not None
    assert reloaded.id == state.id
    assert reloaded.domain == "meas"
    assert len(reloaded.entities) == 2
    assert reloaded.phase == SessionPhase.CONSENT
    assert reloaded.consent_given is False


def test_load_state_returns_none_for_unknown_session(tmp_path):
    assert load_state(tmp_path, "does-not-exist") is None


def test_grant_consent_sets_flag_and_advances_phase(tmp_path, sample_config, sample_variant):
    start_new_session(tmp_path, "2026-09-15-meas", sample_config, sample_variant)

    state = grant_consent(tmp_path, "2026-09-15-meas")

    assert state.consent_given is True
    assert state.phase == SessionPhase.SCOPE
    reloaded = load_state(tmp_path, "2026-09-15-meas")
    assert reloaded.consent_given is True


def test_save_state_roundtrips_mutations(tmp_path, sample_config, sample_variant):
    state = start_new_session(tmp_path, "2026-09-15-meas", sample_config, sample_variant)
    state.paused = True
    save_state(tmp_path, "2026-09-15-meas", state)

    reloaded = load_state(tmp_path, "2026-09-15-meas")
    assert reloaded.paused is True
