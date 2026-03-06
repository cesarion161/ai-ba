"""Build workflow graph from dynamic JSON (similar to instantiate_workflow but from JSON)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_node import NodeEdge, NodeStatus, NodeType, WorkflowNode


async def build_graph_from_json(
    session: AsyncSession,
    project_id: uuid.UUID,
    graph_json: dict,
) -> list[WorkflowNode]:
    """Create WorkflowNode + NodeEdge records from a graph JSON dict."""
    slug_to_node: dict[str, WorkflowNode] = {}

    # Create all nodes
    for node_data in graph_json["nodes"]:
        node = WorkflowNode(
            project_id=project_id,
            slug=node_data["slug"],
            label=node_data["label"],
            branch=node_data.get("branch", "default"),
            node_type=NodeType(node_data["node_type"]),
            status=NodeStatus.PENDING,
            requires_approval=node_data.get("requires_approval", True),
            config=node_data.get("config"),
        )
        session.add(node)
        slug_to_node[node_data["slug"]] = node

    await session.flush()

    # Build dependency map from edges
    deps_for: dict[str, set[str]] = {}
    for edge_data in graph_json.get("edges", []):
        from_slug = edge_data["from_slug"]
        to_slug = edge_data["to_slug"]
        if from_slug in slug_to_node and to_slug in slug_to_node:
            edge = NodeEdge(
                from_node_id=slug_to_node[from_slug].id,
                to_node_id=slug_to_node[to_slug].id,
            )
            session.add(edge)
            deps_for.setdefault(to_slug, set()).add(from_slug)

    # Mark root nodes (no incoming edges) as READY
    for slug, node in slug_to_node.items():
        if slug not in deps_for:
            node.status = NodeStatus.READY

    await session.flush()
    return list(slug_to_node.values())
