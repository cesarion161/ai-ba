from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.worker import celery_app

logger = structlog.get_logger()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
)
def run_workflow_task(self: Any, project_id: str) -> dict:
    """Run the workflow DAG for a project."""
    logger.info("Starting workflow", project_id=project_id, task_id=self.request.id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run_workflow(project_id))
        return result
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
)
def resume_workflow_task(self: Any, project_id: str, node_slug: str, decision: str) -> dict:
    """Resume a paused workflow after HITL decision."""
    logger.info(
        "Resuming workflow",
        project_id=project_id,
        node_slug=node_slug,
        decision=decision,
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_resume_workflow(project_id, node_slug, decision))
        return result
    finally:
        loop.close()


def _make_session_factory():
    """Create a fresh async engine + session factory for the current event loop."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _run_workflow(project_id: str) -> dict:
    from app.engine.orchestrator import build_workflow_graph

    import uuid as _uuid

    from app.models.project import Project

    session_factory = _make_session_factory()

    # Load requirements summary and reset stale running nodes
    async with session_factory() as session:
        from sqlalchemy import select

        from app.models.workflow_node import NodeStatus, WorkflowNode

        pid = _uuid.UUID(project_id)
        project = await session.get(Project, pid)
        requirements_summary = project.requirements_summary or "" if project else ""

        # Reset any stuck "running" nodes back to "ready" so they get picked up
        stale = await session.execute(
            select(WorkflowNode).where(
                WorkflowNode.project_id == pid,
                WorkflowNode.status == NodeStatus.RUNNING,
            )
        )
        for node in stale.scalars().all():
            logger.info("Resetting stale running node", slug=node.slug)
            node.status = NodeStatus.READY
            node.started_at = None
        await session.commit()

    graph = build_workflow_graph(session_factory=session_factory)
    compiled = graph.compile()

    initial_state: dict[str, Any] = {
        "project_id": project_id,
        "requirements_summary": requirements_summary,
        "node_results": {},
        "completed_slugs": [],
        "hitl_node_slug": None,
        "error": None,
    }

    config = {"configurable": {"thread_id": project_id}}

    await compiled.ainvoke(initial_state, config=config)  # type: ignore[arg-type]

    # Update project phase based on final state
    import uuid

    from app.models.project import Project
    from app.models.workflow_node import NodeStatus, WorkflowNode
    from sqlalchemy import select, func, and_

    async with session_factory() as session:
        pid = uuid.UUID(project_id)
        # Check if any nodes are still awaiting review (HITL paused)
        awaiting = await session.execute(
            select(func.count()).select_from(WorkflowNode).where(
                and_(WorkflowNode.project_id == pid, WorkflowNode.status == NodeStatus.AWAITING_REVIEW)
            )
        )
        project = await session.get(Project, pid)
        if project:
            if awaiting.scalar() > 0:
                project.chat_phase = "executing"  # still in progress, waiting for reviews
            else:
                project.chat_phase = "completed"
            await session.commit()

    return {"status": "completed", "project_id": project_id}


async def _resume_workflow(project_id: str, node_slug: str, decision: str) -> dict:
    from langgraph.types import Command

    from app.engine.orchestrator import build_workflow_graph

    session_factory = _make_session_factory()
    graph = build_workflow_graph(session_factory=session_factory)
    compiled = graph.compile()

    config = {"configurable": {"thread_id": project_id}}

    await compiled.ainvoke(
        Command(resume=decision),
        config=config,  # type: ignore[arg-type]
    )
    return {"status": "resumed", "project_id": project_id, "node_slug": node_slug}
