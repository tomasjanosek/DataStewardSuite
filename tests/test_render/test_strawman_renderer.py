from __future__ import annotations

from pathlib import Path

from src.render.strawman_renderer import render_strawman

SNAPSHOT = Path(__file__).parent / "__snapshots__" / "strawman_meas.md"


def test_render_strawman_matches_snapshot(sample_strawman):
    rendered = render_strawman(sample_strawman)
    expected = SNAPSHOT.read_text(encoding="utf-8")
    assert rendered == expected


def test_render_strawman_counts_all_questions(sample_strawman):
    rendered = render_strawman(sample_strawman)
    assert "Otázky pro stewarda (2)" in rendered
