from __future__ import annotations

from pydantic import BaseModel

from src.models.attribute import Attribute
from src.models.process_step import ProcessStep
from src.models.provenance import Provenance
from src.models.quality_rule import QualityRule


class Entity(BaseModel):
    id: str
    name: str
    domain: str
    business_definition: str
    grain: str
    identifier: str
    physical_mapping: list[str] = []
    attributes: list[Attribute] = []
    lifecycle: list[ProcessStep] = []
    quality_rules: list[QualityRule] = []
    known_issues: list[str] = []
    open_questions: list[str] = []
    provenance: Provenance
