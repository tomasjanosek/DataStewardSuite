from __future__ import annotations

from pathlib import Path

import git

from src.models.domain_card import DomainCard
from src.models.entity import Entity
from src.render.domain_card_renderer import render_domain_card
from src.render.entity_renderer import render_entity
from src.render.slug import slugify


class VaultWriter:
    """Renders artifacts to markdown and commits them into the vault git repo.

    # TODO(mvp): vault is a plain local git repo the app owns (git-initialized on first
    # use if it doesn't exist yet); it is not pushed to any remote. Wiring it up as a
    # separate hosted repo/submodule is out of scope for the MVP.
    """

    def __init__(self, vault_path: Path | str) -> None:
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        if (self.vault_path / ".git").exists():
            self.repo = git.Repo(self.vault_path)
        else:
            self.repo = git.Repo.init(self.vault_path)

    def _domain_dir(self, domain_id: str) -> Path:
        return self.vault_path / "domains" / domain_id

    def _known_entity_slugs(self, domain_id: str) -> set[str]:
        entities_dir = self._domain_dir(domain_id) / "entities"
        if not entities_dir.exists():
            return set()
        return {p.stem for p in entities_dir.glob("*.md")}

    def write_domain_card(self, card: DomainCard) -> Path:
        known_slugs = self._known_entity_slugs(card.id) | {
            slugify(ref.name) for ref in card.entities
        }
        content = render_domain_card(card, known_entity_slugs=known_slugs)
        path = self._domain_dir(card.id) / "index.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_entity(self, entity: Entity) -> Path:
        content = render_entity(entity)
        path = self._domain_dir(entity.domain) / "entities" / f"{slugify(entity.name)}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def commit(self, session_id: str, message: str) -> str | None:
        """Stages and commits everything currently written. Returns the commit sha,
        or None if there was nothing to commit."""
        self.repo.git.add(all=True)
        has_head = self.repo.head.is_valid()
        if has_head and not self.repo.index.diff("HEAD"):
            return None
        if not has_head and not self.repo.index.entries:
            return None
        commit = self.repo.index.commit(f"{message}\n\nsession_id: {session_id}")
        return commit.hexsha
