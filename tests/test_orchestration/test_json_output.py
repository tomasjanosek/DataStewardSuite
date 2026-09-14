from __future__ import annotations

import pytest
from pydantic import BaseModel

from src.orchestration.json_output import parse_json_output


class _Dummy(BaseModel):
    name: str
    count: int


def test_parse_json_output_extracts_object_from_surrounding_text():
    raw = 'Thought: here it is\n{"name": "meas", "count": 3}\nThanks!'
    result = parse_json_output(raw, _Dummy)
    assert result == _Dummy(name="meas", count=3)


def test_parse_json_output_raises_when_no_json_present():
    with pytest.raises(ValueError):
        parse_json_output("no json here", _Dummy)


def test_parse_json_output_repairs_minor_malformed_json():
    # missing comma between fields — the kind of slip a long LLM completion can make
    raw = '{"name": "meas" "count": 3}'
    result = parse_json_output(raw, _Dummy)
    assert result == _Dummy(name="meas", count=3)
