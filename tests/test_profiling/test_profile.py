from __future__ import annotations

import pandas as pd
import pytest

from src.profiling.profile import load_profile, run_profile, write_profile
from src.tools.excel_source import ExcelDataSource


@pytest.fixture
def excel_path(tmp_path):
    path = tmp_path / "meas.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"id": [1, 2, 3], "stav": ["a", "a", None]}).to_excel(
            writer, sheet_name="mereni_mista", index=False
        )
    return path


def test_run_and_write_and_load_profile_roundtrip(tmp_path, excel_path):
    source = ExcelDataSource(excel_path)
    profile = run_profile(source, "meas")

    assert profile.domain == "meas"
    assert len(profile.tables) == 1
    assert profile.tables[0].row_count == 3

    out_path = write_profile(profile, tmp_path / "meas.json")
    loaded = load_profile(out_path)
    assert loaded.tables[0].table == "mereni_mista"
    assert loaded.tables[0].columns[1].null_count == 1
