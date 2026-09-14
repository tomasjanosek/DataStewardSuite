from __future__ import annotations

from src.models.entity import Entity
from src.render.markdown_utils import EMPTY_MARK, bullets, render_frontmatter


def render_entity(entity: Entity, domain_index_slug: str = "index") -> str:
    """Deterministically renders an Entity to markdown with YAML frontmatter."""
    frontmatter = render_frontmatter(
        {
            "id": entity.id,
            "name": entity.name,
            "domain": entity.domain,
            "identifier": entity.identifier,
            "status": entity.provenance.status,
            "physical_mapping": list(entity.physical_mapping),
        }
    )

    lines: list[str] = [
        "---",
        frontmatter,
        "---",
        "",
        f"# {entity.name}",
        "",
        f"[[{domain_index_slug}|← zpět na doménu]]",
        "",
        "## Definice",
        "",
        entity.business_definition,
        "",
        "## Granularita",
        "",
        entity.grain,
        "",
        "## Identifikátor",
        "",
        f"`{entity.identifier}`",
        "",
        "## Fyzické mapování",
        "",
    ]
    lines += bullets(entity.physical_mapping)

    lines += ["", "## Atributy", ""]
    if not entity.attributes:
        lines.append(EMPTY_MARK)
    else:
        for attr in entity.attributes:
            mandatory = "povinný" if attr.mandatory else "nepovinný"
            meaning = attr.business_meaning.rstrip().rstrip(".")
            lines.append(
                f"- **{attr.name}** (`{attr.physical_column}`, {mandatory}) — "
                f"{meaning}. Zdroj pravdy: {attr.source_of_truth}."
            )

    lines += ["", "## Proces vzniku dat", ""]
    if not entity.lifecycle:
        lines.append(EMPTY_MARK)
    else:
        for step in sorted(entity.lifecycle, key=lambda s: s.order):
            lines.append(
                f"{step.order}. **{step.actor}** v systému **{step.system}** — "
                f"{step.trigger}: {step.action}"
            )

    lines += ["", "## Pravidla kvality", ""]
    if not entity.quality_rules:
        lines.append(EMPTY_MARK)
    else:
        for rule in entity.quality_rules:
            baseline = rule.baseline_result or "*(baseline zatím neměřena)*"
            threshold = rule.proposed_threshold or "*(práh zatím nenavržen)*"
            lines.append(f"- **{rule.id}**: {rule.description_nl}")
            lines.append(f"  - Baseline: {baseline}")
            lines.append(f"  - Navržený práh: {threshold}")
            if rule.owner:
                lines.append(f"  - Vlastník: {rule.owner}")

    lines += ["", "## Známé problémy", ""]
    lines += bullets(entity.known_issues)

    lines += ["", "## Otevřené otázky", ""]
    lines += bullets(entity.open_questions)

    lines.append("")
    return "\n".join(lines)
