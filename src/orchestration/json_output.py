from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel

_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)

ModelT = TypeVar("ModelT", bound=BaseModel)


def json_schema_instruction(model: type[BaseModel]) -> str:
    """A prompt block stating the exact JSON schema the model must follow.

    Needed because run_architect/run_domain_expert ask the model for raw JSON
    (see parse_json_output's docstring) instead of using crewai's output_pydantic,
    which would otherwise convey the schema via function-calling — without it, the
    model has no reliable way to know the exact field names/shape expected.
    """
    schema = json.dumps(model.model_json_schema(), ensure_ascii=False)
    return f"Přesné JSON schéma, které MUSÍŠ dodržet (žádná jiná pole, žádná jiná struktura):\n{schema}"


def parse_json_output(raw: str, model: type[ModelT]) -> ModelT:
    """Extracts a JSON object from a raw LLM completion and validates it.

    # TODO(mvp): crewai 0.203.2's `Task(output_pydantic=...)` routes through
    # `InternalInstructor`, which makes a *second* LLM call to coerce output into
    # the Pydantic model and does not forward the agent's configured `max_tokens` —
    # it silently truncates on anything but small outputs (confirmed against the
    # installed version; see architect_crew/domain_expert_crew, which ask the model
    # for raw JSON directly and parse it here instead of relying on that path).
    """
    match = _JSON_PATTERN.search(raw)
    if not match:
        raise ValueError(f"No JSON object found in LLM output: {raw!r}")
    return model.model_validate(json.loads(match.group(0)))
