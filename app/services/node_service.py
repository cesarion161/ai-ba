from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import NodeArtifact
from app.models.workflow_node import NodeStatus, WorkflowNode
from app.services import audit_service

VALID_TRANSITIONS: dict[NodeStatus, set[NodeStatus]] = {
    NodeStatus.PENDING: {NodeStatus.READY, NodeStatus.SKIPPED},
    NodeStatus.READY: {NodeStatus.RUNNING, NodeStatus.SKIPPED},
    NodeStatus.RUNNING: {NodeStatus.AWAITING_REVIEW, NodeStatus.APPROVED, NodeStatus.FAILED},
    NodeStatus.AWAITING_REVIEW: {NodeStatus.APPROVED, NodeStatus.REJECTED},
    NodeStatus.REJECTED: {NodeStatus.RUNNING},
    NodeStatus.FAILED: {NodeStatus.RUNNING, NodeStatus.SKIPPED},
    NodeStatus.APPROVED: set(),
    NodeStatus.SKIPPED: set(),
}


class InvalidTransitionError(Exception):
    pass


def validate_transition(current: NodeStatus, target: NodeStatus) -> None:
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(f"Cannot transition from {current.value} to {target.value}")


async def get_node(session: AsyncSession, project_id: uuid.UUID, slug: str) -> WorkflowNode | None:
    result = await session.execute(
        select(WorkflowNode).where(
            WorkflowNode.project_id == project_id,
            WorkflowNode.slug == slug,
        )
    )
    return result.scalar_one_or_none()


async def list_nodes(
    session: AsyncSession,
    project_id: uuid.UUID,
    branch: str | None = None,
    status: str | None = None,
    node_type: str | None = None,
) -> list[WorkflowNode]:
    query = select(WorkflowNode).where(WorkflowNode.project_id == project_id)
    if branch:
        query = query.where(WorkflowNode.branch == branch)
    if status:
        query = query.where(WorkflowNode.status == status)
    if node_type:
        query = query.where(WorkflowNode.node_type == node_type)
    result = await session.execute(query)
    return list(result.scalars().all())


async def approve_node(session: AsyncSession, node: WorkflowNode) -> WorkflowNode:
    validate_transition(node.status, NodeStatus.APPROVED)
    node.status = NodeStatus.APPROVED
    node.completed_at = datetime.now(UTC)
    await audit_service.record(
        session, "approve", "node", entity_id=node.id, project_id=node.project_id
    )
    await session.commit()
    await session.refresh(node)
    return node


async def reject_node(session: AsyncSession, node: WorkflowNode, feedback: str) -> WorkflowNode:
    validate_transition(node.status, NodeStatus.REJECTED)
    node.status = NodeStatus.REJECTED
    node.user_feedback = feedback
    await audit_service.record(
        session,
        "reject",
        "node",
        entity_id=node.id,
        project_id=node.project_id,
        details={"feedback": feedback},
    )
    await session.commit()
    await session.refresh(node)
    return node


async def update_node_output(
    session: AsyncSession, node: WorkflowNode, output_data: dict
) -> WorkflowNode:
    node.output_data = output_data
    node.status = NodeStatus.APPROVED
    node.completed_at = datetime.now(UTC)

    # Create new artifact version
    max_version = 0
    existing = await session.execute(
        select(NodeArtifact)
        .where(NodeArtifact.node_id == node.id)
        .order_by(NodeArtifact.version.desc())
    )
    latest = existing.scalars().first()
    if latest:
        max_version = latest.version

    artifact = NodeArtifact(
        node_id=node.id,
        title=f"{node.label} (edited)",
        content=str(output_data),
        version=max_version + 1,
    )
    session.add(artifact)
    await audit_service.record(
        session,
        "edit_output",
        "node",
        entity_id=node.id,
        project_id=node.project_id,
    )
    await session.commit()
    await session.refresh(node)
    return node


async def retry_node(session: AsyncSession, node: WorkflowNode) -> WorkflowNode:
    if node.status not in (NodeStatus.FAILED, NodeStatus.REJECTED):
        raise InvalidTransitionError(f"Cannot retry node in status {node.status.value}")
    node.status = NodeStatus.READY
    node.retry_count += 1
    await audit_service.record(
        session,
        "retry",
        "node",
        entity_id=node.id,
        project_id=node.project_id,
        details={"retry_count": node.retry_count},
    )
    await session.commit()
    await session.refresh(node)
    return node


async def skip_node(session: AsyncSession, node: WorkflowNode) -> WorkflowNode:
    validate_transition(node.status, NodeStatus.SKIPPED)
    node.status = NodeStatus.SKIPPED
    node.completed_at = datetime.now(UTC)
    await audit_service.record(
        session,
        "skip",
        "node",
        entity_id=node.id,
        project_id=node.project_id,
    )
    await session.commit()
    await session.refresh(node)
    return node


async def submit_answers(session: AsyncSession, node: WorkflowNode, answers: dict) -> WorkflowNode:
    node.output_data = {"answers": answers}
    node.status = NodeStatus.APPROVED
    node.completed_at = datetime.now(UTC)
    await audit_service.record(
        session,
        "answer",
        "node",
        entity_id=node.id,
        project_id=node.project_id,
    )
    await session.commit()
    await session.refresh(node)
    return node
