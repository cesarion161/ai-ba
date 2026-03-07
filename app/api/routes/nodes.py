from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.node import (
    AnswerRequest,
    NodeListResponse,
    NodeResponse,
    OutputEditRequest,
    RejectRequest,
)
from app.models.database import get_db
from app.services import node_service
from app.services.node_service import InvalidTransitionError

router = APIRouter(prefix="/api/projects/{project_id}/nodes", tags=["nodes"])


async def _get_node_or_404(
    db: AsyncSession, project_id: uuid.UUID, slug: str
) -> node_service.WorkflowNode:
    node = await node_service.get_node(db, project_id, slug)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{slug}' not found")
    return node


@router.get("", response_model=NodeListResponse)
async def list_nodes(
    project_id: uuid.UUID,
    branch: str | None = None,
    status: str | None = None,
    node_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> NodeListResponse:
    nodes = await node_service.list_nodes(db, project_id, branch, status, node_type)
    return NodeListResponse(nodes=[NodeResponse.model_validate(n) for n in nodes])


@router.get("/{slug}", response_model=NodeResponse)
async def get_node(
    project_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    node = await _get_node_or_404(db, project_id, slug)
    return NodeResponse.model_validate(node)


@router.post("/{slug}/approve", response_model=NodeResponse)
async def approve_node(
    project_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    node = await _get_node_or_404(db, project_id, slug)
    try:
        node = await node_service.approve_node(db, node)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Trigger workflow continuation for any newly-ready nodes
    await _continue_workflow(db, project_id)

    return NodeResponse.model_validate(node)


@router.post("/{slug}/reject", response_model=NodeResponse)
async def reject_node(
    project_id: uuid.UUID,
    slug: str,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    node = await _get_node_or_404(db, project_id, slug)
    try:
        node = await node_service.reject_node(db, node, body.feedback)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return NodeResponse.model_validate(node)


@router.put("/{slug}/output", response_model=NodeResponse)
async def edit_output(
    project_id: uuid.UUID,
    slug: str,
    body: OutputEditRequest,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    node = await _get_node_or_404(db, project_id, slug)
    node = await node_service.update_node_output(db, node, body.output_data)
    return NodeResponse.model_validate(node)


@router.post("/{slug}/retry", response_model=NodeResponse)
async def retry_node(
    project_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    node = await _get_node_or_404(db, project_id, slug)
    try:
        node = await node_service.retry_node(db, node)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return NodeResponse.model_validate(node)


@router.post("/{slug}/skip", response_model=NodeResponse)
async def skip_node(
    project_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    node = await _get_node_or_404(db, project_id, slug)
    try:
        node = await node_service.skip_node(db, node)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await _continue_workflow(db, project_id)

    return NodeResponse.model_validate(node)


@router.get("/{slug}/questions")
async def get_node_questions(
    project_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the questions an ask_user node wants the user to answer."""
    node = await _get_node_or_404(db, project_id, slug)
    if node.node_type.value != "ask_user":
        raise HTTPException(status_code=400, detail=f"Node '{slug}' is not an ask_user node")
    questions = (node.config or {}).get("questions", [])
    return {
        "slug": node.slug,
        "label": node.label,
        "status": node.status.value,
        "questions": [{"index": i, "question": q} for i, q in enumerate(questions)],
    }


@router.post("/{slug}/answer", response_model=NodeResponse)
async def answer_node(
    project_id: uuid.UUID,
    slug: str,
    body: AnswerRequest,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    node = await _get_node_or_404(db, project_id, slug)
    node = await node_service.submit_answers(db, node, body.answers)
    return NodeResponse.model_validate(node)


async def _continue_workflow(db: AsyncSession, project_id: uuid.UUID) -> None:
    """If there are newly READY nodes, kick off a Celery task to process them."""
    from sqlalchemy import select, func, and_

    from app.models.workflow_node import NodeStatus, WorkflowNode

    ready_count_result = await db.execute(
        select(func.count()).select_from(WorkflowNode).where(
            and_(
                WorkflowNode.project_id == project_id,
                WorkflowNode.status == NodeStatus.READY,
            )
        )
    )
    ready_count = ready_count_result.scalar()

    if ready_count > 0:
        from app.services import project_service
        from app.tasks.workflow_tasks import run_workflow_task

        project = await project_service.get_project(db, project_id)
        if project and project.chat_phase != "executing":
            project.chat_phase = "executing"
            await db.commit()

        run_workflow_task.delay(str(project_id))
    else:
        # Check if all nodes are done (no pending, ready, or running)
        from app.services import project_service

        incomplete = await db.execute(
            select(func.count()).select_from(WorkflowNode).where(
                and_(
                    WorkflowNode.project_id == project_id,
                    WorkflowNode.status.in_([
                        NodeStatus.PENDING, NodeStatus.READY,
                        NodeStatus.RUNNING, NodeStatus.AWAITING_REVIEW,
                    ]),
                )
            )
        )
        if incomplete.scalar() == 0:
            project = await project_service.get_project(db, project_id)
            if project:
                project.chat_phase = "completed"
                await db.commit()
