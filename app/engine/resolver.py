from __future__ import annotations

import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_node import NodeEdge, NodeStatus, WorkflowNode


async def resolve_ready_nodes(session: AsyncSession, project_id: uuid.UUID) -> list[WorkflowNode]:
    """Find READY nodes and PENDING nodes whose ALL upstream deps are done."""

    # Subquery: nodes that have at least one non-completed upstream dependency
    blocked_nodes = (
        select(NodeEdge.to_node_id)
        .join(WorkflowNode, WorkflowNode.id == NodeEdge.from_node_id)
        .where(WorkflowNode.status.notin_([NodeStatus.APPROVED, NodeStatus.SKIPPED]))
        .distinct()
        .scalar_subquery()
    )

    # Find PENDING nodes not in the blocked set and promote them to READY
    pending_result = await session.execute(
        select(WorkflowNode).where(
            and_(
                WorkflowNode.project_id == project_id,
                WorkflowNode.status == NodeStatus.PENDING,
                WorkflowNode.id.notin_(blocked_nodes),
            )
        )
    )
    newly_ready = list(pending_result.scalars().all())

    for node in newly_ready:
        node.status = NodeStatus.READY

    if newly_ready:
        await session.flush()

    # Return all READY nodes (including those already marked READY during graph creation)
    ready_result = await session.execute(
        select(WorkflowNode).where(
            and_(
                WorkflowNode.project_id == project_id,
                WorkflowNode.status == NodeStatus.READY,
            )
        )
    )
    return list(ready_result.scalars().all())


async def propagate_completion(session: AsyncSession, node_id: uuid.UUID) -> list[WorkflowNode]:
    """After a node is approved/skipped, check and mark downstream nodes as READY."""
    # Find downstream nodes
    downstream_edges = await session.execute(
        select(NodeEdge.to_node_id).where(NodeEdge.from_node_id == node_id)
    )
    downstream_ids = [row[0] for row in downstream_edges.all()]

    if not downstream_ids:
        return []

    newly_ready = []
    for ds_id in downstream_ids:
        ds_node = await session.get(WorkflowNode, ds_id)
        if not ds_node or ds_node.status != NodeStatus.PENDING:
            continue

        # Check if ALL upstream deps are done
        upstream_incomplete = await session.execute(
            select(func.count())
            .select_from(NodeEdge)
            .join(WorkflowNode, WorkflowNode.id == NodeEdge.from_node_id)
            .where(
                and_(
                    NodeEdge.to_node_id == ds_id,
                    WorkflowNode.status.notin_([NodeStatus.APPROVED, NodeStatus.SKIPPED]),
                )
            )
        )
        if upstream_incomplete.scalar() == 0:
            ds_node.status = NodeStatus.READY
            newly_ready.append(ds_node)

    if newly_ready:
        await session.flush()

    return newly_ready
