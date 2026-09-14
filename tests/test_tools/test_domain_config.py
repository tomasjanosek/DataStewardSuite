from __future__ import annotations

from pathlib import Path

from src.tools.domain_config import load_domain_config

CONFIG_PATH = Path(__file__).parents[2] / "config" / "domains" / "meas.yaml"


def test_load_meas_domain_config():
    config = load_domain_config(CONFIG_PATH)

    assert config.domain == "meas"
    assert config.steward
    assert config.what_would_prove_us_wrong
    assert "CORE ZONE > Measuring" in config.model_scope.folders
    assert any(p.startswith("^LZ_SCADA_") for p in config.model_scope.table_code_patterns)
