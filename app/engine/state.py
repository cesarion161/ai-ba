from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


def merge_node_results(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing}
    merged.update(new)
    return merged


def keep_first_error(existing: str | None, new: str | None) -> str | None:
    """Keep the first error encountered."""
    return existing or new


class WorkflowState(TypedDict, total=False):
    project_id: str
    requirements_summary: str
    node_results: Annotated[dict[str, Any], merge_node_results]
    current_node_slug: str
    completed_slugs: Annotated[list[str], operator.add]
    ready_slugs: list[str]
    hitl_node_slug: str | None
    error: Annotated[str | None, keep_first_error]
