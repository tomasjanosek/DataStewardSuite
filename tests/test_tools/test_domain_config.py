from __future__ import annotations

from pathlib import Path

from src.tools.domain_config import load_domain_config

DOMAINS_DIR = Path(__file__).parents[2] / "config" / "domains"


def test_load_meas_domain_config():
    config = load_domain_config(DOMAINS_DIR / "meas.yaml")

    assert config.domain == "meas"
    assert config.steward
    assert config.what_would_prove_us_wrong
    assert "CORE ZONE > Measuring" in config.model_scope.folders
    assert any(p.startswith("^LZ_SCADA_") for p in config.model_scope.table_code_patterns)


def test_load_procurement_domain_config():
    config = load_domain_config(DOMAINS_DIR / "procurement.yaml")

    assert config.domain == "procurement"
    assert config.what_would_prove_us_wrong
    assert "DATAMARTS > DM_PROCMT" in config.model_scope.folders
    assert any(p.startswith("^TEND_") for p in config.model_scope.table_code_patterns)
    assert any(p.startswith("^LZ_TBOX_") for p in config.model_scope.table_code_patterns)
