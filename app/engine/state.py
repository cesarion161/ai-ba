from __future__ import annotations

from typing import Annotated, Any, TypedDict


def merge_node_results(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing}
    merged.update(new)
    return merged


class WorkflowState(TypedDict, total=False):
    project_id: str
    node_results: Annotated[dict[str, Any], merge_node_results]
    current_node_slug: str
    completed_slugs: list[str]
    hitl_node_slug: str | None
    error: str | None
