from __future__ import annotations

from src.models.domain_card import DomainCard
from src.render.markdown_utils import EMPTY_MARK, bullets, render_frontmatter
from src.render.slug import slugify


def render_domain_card(card: DomainCard, known_entity_slugs: set[str]) -> str:
    """Deterministically renders a DomainCard to markdown with YAML frontmatter.

    `known_entity_slugs` are the entity file slugs that already exist in the vault;
    only those get turned into [[wikilinks]] so no dead links are created.
    """
    frontmatter = render_frontmatter(
        {
            "id": card.id,
            "name": card.name,
            "steward": card.steward,
            "status": card.status,
            "source_systems": list(card.source_systems),
        }
    )

    lines: list[str] = ["---", frontmatter, "---", "", f"# {card.name}", ""]

    lines += ["## Rozsah domény", "", "### Patří do domény", ""]
    lines += bullets(card.scope_in)
    lines += ["", "### Nepatří do domény", ""]
    lines += bullets(card.scope_out)

    lines += ["", "## Zdrojové systémy", ""]
    lines += bullets(card.source_systems)

    lines += ["", "## Entity", ""]
    if not card.entities:
        lines.append(EMPTY_MARK)
    else:
        for ref in card.entities:
            slug = slugify(ref.name)
            label = f"[[{slug}|{ref.name}]]" if slug in known_entity_slugs else ref.name
            lines.append(f"- {label} — `{ref.status}`")

    lines += ["", "## Rozhodnutí", ""]
    if not card.decisions:
        lines.append(EMPTY_MARK)
    else:
        for decision in card.decisions:
            lines.append(
                f"- **{decision.text}** — rozhodl(a) {decision.decided_by}, "
                f"{decision.decided_at:%Y-%m-%d}"
            )

    lines += ["", "## Otevřené body", ""]
    if not card.open_items:
        lines.append(EMPTY_MARK)
    else:
        for item in card.open_items:
            owner = item.proposed_owner or "*(bez vlastníka)*"
            lines.append(f"- [{item.status}] ({item.type}) {item.text} — {owner}")

    lines.append("")
    return "\n".join(lines)
