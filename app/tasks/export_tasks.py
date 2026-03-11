from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.worker import celery_app

logger = structlog.get_logger()


def _make_session_factory() -> Any:
    """Create a fresh async engine + session factory for the current event loop."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def export_to_notion_task(self: Any, project_id: str) -> dict:
    """Export project documents to Notion."""
    logger.info("Starting Notion export", project_id=project_id, task_id=self.request.id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run_export(project_id))
        return result
    except Exception as e:
        logger.error("notion_export_failed", project_id=project_id, error=str(e))
        loop.run_until_complete(_publish_failed(project_id, str(e)))
        if self.request.retries < 2:
            raise self.retry(exc=e, countdown=10 * (self.request.retries + 1))
        return {"status": "failed", "project_id": project_id, "error": str(e)}
    finally:
        loop.close()


async def _run_export(project_id: str) -> dict:
    import uuid as _uuid

    from sqlalchemy import select

    from app.models.project import Project
    from app.models.workflow_node import NodeStatus, WorkflowNode
    from app.services.event_bus import (
        EXPORT_COMPLETED,
        EXPORT_PROGRESS,
        EXPORT_STARTED,
        event_bus,
    )
    from app.services.notion_export import NotionExportService

    session_factory = _make_session_factory()
    pid = _uuid.UUID(project_id)

    async with session_factory() as session:
        project = await session.get(Project, pid)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        project_name = project.name
        existing_page_id = project.notion_page_id

        # Collect all completed document nodes
        result = await session.execute(
            select(WorkflowNode).where(
                WorkflowNode.project_id == pid,
                WorkflowNode.status.in_([NodeStatus.APPROVED, NodeStatus.AWAITING_REVIEW]),
                WorkflowNode.output_data.isnot(None),
            )
        )
        nodes = result.scalars().all()

    # Extract documents from node output_data (same logic as format_export)
    documents: list[dict[str, str]] = []
    for node in nodes:
        output = node.output_data or {}
        if "document" in output:
            title = output.get("title", node.label)
            documents.append({"title": title, "markdown": output["document"]})

    if not documents:
        raise ValueError("No completed document nodes found for export")

    # Publish started event
    await event_bus.publish(
        project_id,
        EXPORT_STARTED,
        {"total_documents": len(documents)},
    )

    # Run the export
    service = NotionExportService()
    export_result = service.export_project(
        project_id=project_id,
        project_name=project_name,
        documents=documents,
        existing_page_id=existing_page_id,
    )

    # Wrap coroutine
    result = await export_result

    # Store notion_page_id on project
    async with session_factory() as session:
        project = await session.get(Project, pid)
        if project:
            project.notion_page_id = result.root_page_id
            await session.commit()

    # Publish completed event
    await event_bus.publish(
        project_id,
        EXPORT_COMPLETED,
        {
            "notion_page_id": result.root_page_id,
            "notion_url": result.notion_url,
            "page_count": result.page_count,
        },
    )

    return {
        "status": "completed",
        "project_id": project_id,
        "notion_page_id": result.root_page_id,
        "notion_url": result.notion_url,
        "page_count": result.page_count,
    }


async def _publish_failed(project_id: str, error: str) -> None:
    from app.services.event_bus import EXPORT_FAILED, event_bus

    await event_bus.publish(
        project_id,
        EXPORT_FAILED,
        {"error": error},
    )
