from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator

from src.models.physical_model import PhysicalColumn, PhysicalModelSlice, PhysicalTable

# The catalog export nests each node's real payload as a JSON *string* under
# "actualData" (a stringified duplicate of the node itself, plus detail the outer
# node doesn't carry — columns, comments, lineage). Tree navigation (type/name/code/
# children) is already decoded on the outer node, so only TABLE/MAPPING leaves need
# this second json.loads() to get their detail.
def _parse_actual_data(node: dict[str, Any]) -> dict[str, Any]:
    raw = node.get("actualData")
    if not raw:
        return {}
    return json.loads(raw)


def load_physical_model(path: Path | str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _walk_tables(node: dict[str, Any], folder_path: list[str]) -> Iterator[tuple[list[str], dict[str, Any]]]:
    node_type = node.get("type")
    if node_type == "TABLE":
        yield folder_path, node
        return
    next_path = folder_path + [node.get("name") or node.get("code") or ""] if node_type == "FOLDER" else folder_path
    for child in node.get("children", []) or []:
        yield from _walk_tables(child, next_path)


def _table_matches(
    folder_path: list[str], code: str, folders: list[str], patterns: list[re.Pattern[str]]
) -> bool:
    path_str = " > ".join(folder_path)
    if any(folder in path_str for folder in folders):
        return True
    return any(pattern.search(code) for pattern in patterns)


def _extract_columns(inner: dict[str, Any]) -> list[PhysicalColumn]:
    return [
        PhysicalColumn(
            code=col.get("code", ""),
            name=col.get("name", ""),
            data_type=col.get("dataType", ""),
            mandatory=bool(col.get("notNullFlag", False)),
            business_meaning=col.get("description") or col.get("comment") or "",
            stereotype=(col.get("stereotype") or {}).get("code"),
        )
        for col in inner.get("columns", []) or []
    ]


def _extract_source_tables(table_node: dict[str, Any]) -> list[str]:
    sources: set[str] = set()
    for child in table_node.get("children", []) or []:
        if child.get("type") != "MAPPING":
            continue
        for item in _parse_actual_data(child).get("sourceItems", []) or []:
            if item.get("objectType") == "TABLE" and item.get("objectCode"):
                sources.add(item["objectCode"])
    return sorted(sources)


def load_domain_slice(
    model_path: Path | str,
    domain: str,
    folders: list[str],
    table_code_patterns: list[str],
) -> PhysicalModelSlice:
    """Deterministically filters the physical model export to a domain's candidate slice.

    No LLM involved — see spec section 10.
    """
    root = load_physical_model(model_path)
    patterns = [re.compile(p) for p in table_code_patterns]

    tables: list[PhysicalTable] = []
    for folder_path, node in _walk_tables(root, []):
        code = node.get("code", "")
        if not _table_matches(folder_path, code, folders, patterns):
            continue
        inner = _parse_actual_data(node)
        tables.append(
            PhysicalTable(
                code=code,
                name=node.get("name", ""),
                zone=folder_path[0] if folder_path else "",
                folder_path=folder_path,
                business_meaning=inner.get("description") or inner.get("comment") or "",
                table_kind=inner.get("stereotypeCode"),
                columns=_extract_columns(inner),
                source_tables=_extract_source_tables(node),
            )
        )

    return PhysicalModelSlice(domain=domain, tables=tables)
