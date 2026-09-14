from __future__ import annotations

from src.tools.doc_loader import load_documents


def test_load_documents_reads_files_in_order(tmp_path):
    (tmp_path / "a.md").write_text("# A\nObsah A.", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B\nObsah B.", encoding="utf-8")

    docs = load_documents(tmp_path, ["b.md", "a.md"])

    assert [d.filename for d in docs] == ["b.md", "a.md"]
    assert docs[0].content == "# B\nObsah B."
    assert docs[1].content == "# A\nObsah A."
