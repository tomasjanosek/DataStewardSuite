from __future__ import annotations

from src.tools.doc_loader import list_available_documents, load_documents, sanitize_filename


def test_load_documents_reads_files_in_order(tmp_path):
    (tmp_path / "a.md").write_text("# A\nObsah A.", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B\nObsah B.", encoding="utf-8")

    docs = load_documents(tmp_path, ["b.md", "a.md"])

    assert [d.filename for d in docs] == ["b.md", "a.md"]
    assert docs[0].content == "# B\nObsah B."
    assert docs[1].content == "# A\nObsah A."


def test_list_available_documents_only_lists_md_and_txt(tmp_path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")
    (tmp_path / "c.xlsx").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()

    assert list_available_documents(tmp_path) == ["a.md", "b.txt"]


def test_list_available_documents_missing_dir_returns_empty():
    assert list_available_documents("/does/not/exist") == []


def test_sanitize_filename_strips_directory_components():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("../secret.md") == "secret.md"


def test_sanitize_filename_replaces_unsafe_characters():
    assert sanitize_filename("proces popis (v2)!.md") == "proces_popis__v2__.md"


def test_sanitize_filename_never_returns_empty_or_dots():
    assert sanitize_filename("..") == "upload.txt"
    assert sanitize_filename(".") == "upload.txt"
    assert sanitize_filename("") == "upload.txt"
