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
    try:
        result = loop.run_until_complete(_resume_workflow(project_id, node_slug, decision))
        return result
    finally:
        loop.close()


async def _run_workflow(project_id: str) -> dict:
    from app.engine.orchestrator import build_workflow_graph

    graph = build_workflow_graph()
    compiled = graph.compile()

    initial_state: dict[str, Any] = {
        "project_id": project_id,
        "node_results": {},
        "completed_slugs": [],
        "hitl_node_slug": None,
        "error": None,
    }

    config = {"configurable": {"thread_id": project_id}}

    await compiled.ainvoke(initial_state, config=config)  # type: ignore[arg-type]
    return {"status": "completed", "project_id": project_id}


async def _resume_workflow(project_id: str, node_slug: str, decision: str) -> dict:
    from langgraph.types import Command

    from app.engine.orchestrator import build_workflow_graph

    graph = build_workflow_graph()
    compiled = graph.compile()

    config = {"configurable": {"thread_id": project_id}}

    await compiled.ainvoke(
        Command(resume=decision),
        config=config,  # type: ignore[arg-type]
    )
    return {"status": "resumed", "project_id": project_id, "node_slug": node_slug}
