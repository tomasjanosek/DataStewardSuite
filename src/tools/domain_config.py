from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class ModelScope(BaseModel):
    """Deterministic candidate-slice rule for the domain's physical model tables.

    A table matches if its folder path contains any of `folders` as a substring
    (joined with " > "), OR its code matches any of `table_code_patterns` (regex).

    # TODO(mvp): this is a PREP-phase candidate set only — broad recall is fine,
    # since the steward confirms real scope_in/scope_out during the session
    # (spec section 6, phase 2). Getting it exactly right here is not required.
    """

    folders: list[str] = []
    table_code_patterns: list[str] = []


class DomainConfig(BaseModel):
    domain: str
    name: str
    steward: str
    goal: str
    scope_in: list[str] = []
    scope_out: list[str] = []
    model_scope: ModelScope
    documents: list[str] = []
    what_would_prove_us_wrong: str


def load_domain_config(path: Path | str) -> DomainConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return DomainConfig.model_validate(raw)
