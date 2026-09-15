from __future__ import annotations

import os

from src.models.physical_model import PhysicalModelSlice
from src.tools.data_source import DataSource
from src.tools.excel_source import ExcelDataSource


def build_data_source(model_slice: PhysicalModelSlice | None = None) -> DataSource:
    """DATA_SOURCE_PROVIDER=excel is the verified, demoable offline path.
    DATA_SOURCE_PROVIDER=redshift is the spec's production path — see
    RedshiftDataSource's docstring: unverified, no live cluster was reachable here.
    """
    provider = os.environ.get("DATA_SOURCE_PROVIDER", "excel")

    if provider == "excel":
        return ExcelDataSource(os.environ["EXCEL_DATA_PATH"])

    if provider == "redshift":
        from src.tools.redshift_source import RedshiftDataSource

        if model_slice is None:
            raise ValueError("model_slice is required to build the Redshift table allowlist")
        allowed_tables = {t.code: [c.code for c in t.columns] for t in model_slice.tables}
        return RedshiftDataSource(
            allowed_tables,
            host=os.environ["REDSHIFT_HOST"],
            port=int(os.environ.get("REDSHIFT_PORT", 5439)),
            database=os.environ["REDSHIFT_DATABASE"],
            user=os.environ["REDSHIFT_USER"],
            password=os.environ["REDSHIFT_PASSWORD"],
            schema=os.environ.get("REDSHIFT_SCHEMA", "public"),
        )

    raise ValueError(f"Unknown DATA_SOURCE_PROVIDER: {provider!r}")
