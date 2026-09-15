from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.models.profile import DataProfile
from src.tools.data_source import DataSource


def run_profile(data_source: DataSource, domain: str) -> DataProfile:
    """Precomputes cardinality/nulls/ranges per table. Offline only — never runs
    live during a session (spec section 7)."""
    tables = [data_source.profile_table(t) for t in data_source.list_tables()]
    return DataProfile(domain=domain, measured_at=datetime.now(), tables=tables)


def write_profile(profile: DataProfile, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_profile(path: Path | str) -> DataProfile:
    return DataProfile.model_validate_json(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    import argparse
    import os

    from src.tools.data_source_factory import build_data_source
    from src.tools.domain_config import load_domain_config
    from src.tools.model_loader import load_domain_slice

    parser = argparse.ArgumentParser(description="Precompute a data profile for a domain.")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--model-path", default="data/physical_model.json")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    domain_config = load_domain_config(f"config/domains/{args.domain}.yaml")

    slice_ = None
    if os.environ.get("DATA_SOURCE_PROVIDER", "excel") == "redshift":
        slice_ = load_domain_slice(
            args.model_path,
            domain=domain_config.domain,
            folders=domain_config.model_scope.folders,
            table_code_patterns=domain_config.model_scope.table_code_patterns,
        )
    source = build_data_source(slice_)

    result_profile = run_profile(source, domain_config.domain)
    output_path = args.output or f"data/profiles/{args.domain}.json"
    written_path = write_profile(result_profile, output_path)

    print(f"Profile written to {written_path}")
    for t in result_profile.tables:
        print(f"  {t.table}: {t.row_count} rows, {len(t.columns)} columns")
