from __future__ import annotations

from pathlib import Path

from src.render.domain_card_renderer import render_domain_card

SNAPSHOT = Path(__file__).parent / "__snapshots__" / "domain_card_meas.md"


def test_render_domain_card_matches_snapshot(sample_domain_card):
    rendered = render_domain_card(sample_domain_card, known_entity_slugs={"mereni-mista"})
    expected = SNAPSHOT.read_text(encoding="utf-8")
    assert rendered == expected


def test_render_domain_card_only_links_known_entities(sample_domain_card):
    rendered = render_domain_card(sample_domain_card, known_entity_slugs=set())
    assert "[[mereni-mista|Měření místa]]" not in rendered
    assert "Měření místa" in rendered

    rendered_with_known = render_domain_card(sample_domain_card, known_entity_slugs={"mereni-mista"})
    assert "[[mereni-mista|Měření místa]]" in rendered_with_known
    assert "[[odecty|Odečty]]" not in rendered_with_known
