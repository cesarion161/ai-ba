from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.templates.base import WorkflowTemplate
from app.models.workflow_node import NodeEdge, NodeStatus, WorkflowNode


async def instantiate_workflow(
    session: AsyncSession,
    project_id: uuid.UUID,
    template: WorkflowTemplate,
) -> list[WorkflowNode]:
    slug_to_node: dict[str, WorkflowNode] = {}

    # Create all nodes
    for nt in template.nodes:
        node = WorkflowNode(
            project_id=project_id,
            slug=nt.slug,
            label=nt.label,
            branch=nt.branch,
            node_type=nt.node_type,
            status=NodeStatus.PENDING,
            requires_approval=nt.requires_approval,
            config=nt.config,
        )
        session.add(node)
        slug_to_node[nt.slug] = node

    # Flush to get IDs assigned
    await session.flush()

    # Create edges
    for nt in template.nodes:
        for dep_slug in nt.depends_on:
            edge = NodeEdge(
                from_node_id=slug_to_node[dep_slug].id,
                to_node_id=slug_to_node[nt.slug].id,
            )
            session.add(edge)

    # Mark root nodes (no dependencies) as READY
    root_slugs = template.root_slugs()
    for slug in root_slugs:
        slug_to_node[slug].status = NodeStatus.READY

    await session.flush()
    return list(slug_to_node.values())
