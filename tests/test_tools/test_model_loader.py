from __future__ import annotations

import json

import pytest

from src.tools.model_loader import load_domain_slice


def _table(code: str, name: str, *, columns=None, mapping_sources: list[str] | None = None) -> dict:
    inner = {
        "code": code,
        "name": name,
        "description": f"Popis tabulky {name}.",
        "stereotypeCode": "fact",
        "columns": columns or [],
    }
    children = []
    if mapping_sources:
        mapping_inner = {
            "code": f"MAP_{code}",
            "sourceItems": [
                {"objectType": "TABLE", "objectCode": src, "ownerName": "DW_CORE"}
                for src in mapping_sources
            ],
        }
        children.append(
            {
                "code": f"MAP_{code}",
                "name": f"MAP_{code}",
                "type": "MAPPING",
                "actualData": json.dumps(mapping_inner),
                "children": [],
            }
        )
    return {
        "code": code,
        "name": name,
        "type": "TABLE",
        "actualData": json.dumps(inner),
        "children": children,
    }


def _folder(name: str, children: list[dict]) -> dict:
    return {"name": name, "type": "FOLDER", "actualData": "{}", "children": children}


def _column(code: str, name: str, data_type: str, mandatory: bool, comment: str) -> dict:
    return {
        "code": code,
        "name": name,
        "dataType": data_type,
        "notNullFlag": mandatory,
        "comment": comment,
        "stereotype": {"code": "dw_column"},
    }


@pytest.fixture
def sample_model_file(tmp_path):
    meas_var = _table(
        "MEAS_VAR",
        "Measuring Variable",
        columns=[_column("MEAS_VAR_KEY", "Measuring Variable Key", "VARCHAR(100)", True, "ID proměnné")],
    )
    meas_flow_fact = _table(
        "MEAS_FLOW_FACT",
        "MEAS Flow Fact",
        mapping_sources=["MEAS_VAR"],
    )
    other_fact = _table("OTHER_FACT", "Other Domain Fact")
    lz_scada = _table("LZ_SCADA_CD_STATION", "LZ_SCADA_CD_STATION")

    root = {
        "code": "ADS",
        "name": "Gasnet Data platform",
        "type": "SYSTEM",
        "actualData": "{}",
        "children": [
            _folder("CORE ZONE", [_folder("CORE ZONE", [_folder("Measuring", [meas_var])])]),
            _folder("DATAMARTS", [_folder("DM_MEAS", [meas_flow_fact]), _folder("DM_OTHER", [other_fact])]),
            _folder("LANDING ZONE", [_folder("LANDING ZONE", [_folder("LZ_SCADA", [lz_scada])])]),
        ],
    }
    path = tmp_path / "physical_model.json"
    path.write_text(json.dumps(root), encoding="utf-8")
    return path


def test_load_domain_slice_includes_only_matching_tables(sample_model_file):
    slice_ = load_domain_slice(
        sample_model_file,
        domain="meas",
        folders=["CORE ZONE > Measuring", "DATAMARTS > DM_MEAS"],
        table_code_patterns=["^LZ_SCADA_"],
    )

    codes = {t.code for t in slice_.tables}
    assert codes == {"MEAS_VAR", "MEAS_FLOW_FACT", "LZ_SCADA_CD_STATION"}
    assert "OTHER_FACT" not in codes


def test_load_domain_slice_extracts_columns_and_lineage(sample_model_file):
    slice_ = load_domain_slice(
        sample_model_file,
        domain="meas",
        folders=["CORE ZONE > Measuring", "DATAMARTS > DM_MEAS"],
        table_code_patterns=[],
    )

    by_code = {t.code: t for t in slice_.tables}
    meas_var = by_code["MEAS_VAR"]
    assert meas_var.zone == "CORE ZONE"
    assert meas_var.columns[0].code == "MEAS_VAR_KEY"
    assert meas_var.columns[0].mandatory is True
    assert meas_var.columns[0].business_meaning == "ID proměnné"

    meas_flow_fact = by_code["MEAS_FLOW_FACT"]
    assert meas_flow_fact.source_tables == ["MEAS_VAR"]
