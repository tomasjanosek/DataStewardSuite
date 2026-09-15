from __future__ import annotations

from src.orchestration.prep import load_strawman, write_strawman


def test_write_and_load_strawman_roundtrip(tmp_path, sample_strawman):
    write_strawman(sample_strawman, tmp_path, "2026-09-15-meas")

    assert (tmp_path / "2026-09-15-meas" / "strawman.md").exists()
    assert (tmp_path / "2026-09-15-meas" / "strawman.json").exists()

    loaded = load_strawman(tmp_path, "2026-09-15-meas")
    assert loaded == sample_strawman
