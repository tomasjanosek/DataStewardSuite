from __future__ import annotations

from pathlib import Path

from src.render.entity_renderer import render_entity

SNAPSHOT = Path(__file__).parent / "__snapshots__" / "entity_mereni_mista.md"


def test_render_entity_matches_snapshot(sample_entity):
    rendered = render_entity(sample_entity)
    expected = SNAPSHOT.read_text(encoding="utf-8")
    assert rendered == expected


def test_render_entity_links_back_to_domain_index(sample_entity_2):
    rendered = render_entity(sample_entity_2, domain_index_slug="index")
    assert "[[index|← zpět na doménu]]" in rendered
