from __future__ import annotations

from pathlib import Path

import git

from src.tools.vault_writer import VaultWriter


def test_write_domain_card_and_entity_produce_files_with_frontmatter(tmp_path, sample_domain_card, sample_entity):
    writer = VaultWriter(tmp_path)

    card_path = writer.write_domain_card(sample_domain_card)
    entity_path = writer.write_entity(sample_entity)

    assert card_path == tmp_path / "domains" / "meas" / "index.md"
    assert entity_path == tmp_path / "domains" / "meas" / "entities" / "mereni-mista.md"
    assert card_path.read_text(encoding="utf-8").startswith("---\n")
    assert entity_path.read_text(encoding="utf-8").startswith("---\n")


def test_no_dead_wikilinks_once_entity_is_written(tmp_path, sample_domain_card, sample_entity, sample_entity_2):
    writer = VaultWriter(tmp_path)
    writer.write_entity(sample_entity)
    writer.write_entity(sample_entity_2)
    card_path = writer.write_domain_card(sample_domain_card)

    content = card_path.read_text(encoding="utf-8")
    assert "[[mereni-mista|" in content
    assert "[[odecty|" in content


def test_vault_is_initialized_as_its_own_git_repo(tmp_path, sample_domain_card):
    writer = VaultWriter(tmp_path)
    writer.write_domain_card(sample_domain_card)

    assert (tmp_path / ".git").exists()
    repo = git.Repo(tmp_path)
    assert repo.bare is False


def test_commit_records_session_id_and_is_idempotent_when_nothing_changed(tmp_path, sample_domain_card):
    writer = VaultWriter(tmp_path)
    writer.write_domain_card(sample_domain_card)

    sha = writer.commit(session_id="2026-09-14-meas", message="Update domain card")
    assert sha is not None

    commit = writer.repo.commit(sha)
    assert "session_id: 2026-09-14-meas" in commit.message

    second_sha = writer.commit(session_id="2026-09-14-meas", message="Nothing changed")
    assert second_sha is None


def test_reusing_an_existing_vault_path_does_not_reinit_git(tmp_path, sample_domain_card):
    first = VaultWriter(tmp_path)
    first.write_domain_card(sample_domain_card)
    first.commit(session_id="2026-09-14-meas", message="Initial")
    first_head = first.repo.head.commit.hexsha

    second = VaultWriter(tmp_path)
    assert second.repo.head.commit.hexsha == first_head
