from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.database import get_db
from app.models.project import Project
from app.models.workflow_node import NodeStatus, WorkflowNode

router = APIRouter(prefix="/api/projects/{project_id}/exports", tags=["exports"])


class NotionExportResponse(BaseModel):
    task_id: str
    status: str


class NotionExportStatusResponse(BaseModel):
    exported: bool
    notion_page_id: str | None
    notion_url: str | None


@router.post("/notion", response_model=NotionExportResponse, status_code=202)
async def export_to_notion(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> NotionExportResponse:
    """Trigger export of project documents to Notion."""
    settings = get_settings()
    if not settings.NOTION_API_TOKEN:
        raise HTTPException(status_code=400, detail="NOTION_API_TOKEN not configured")

    # Verify project exists
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify project has completed document nodes
    result = await db.execute(
        select(WorkflowNode).where(
            WorkflowNode.project_id == project_id,
            WorkflowNode.status.in_([NodeStatus.APPROVED, NodeStatus.AWAITING_REVIEW]),
            WorkflowNode.output_data.isnot(None),
        )
    )
    nodes = result.scalars().all()
    has_documents = any(
        isinstance(n.output_data, dict) and "document" in n.output_data for n in nodes
    )
    if not has_documents:
        raise HTTPException(status_code=400, detail="No completed documents to export")

    from app.tasks.export_tasks import export_to_notion_task

    task = export_to_notion_task.delay(str(project_id))
    return NotionExportResponse(task_id=task.id, status="queued")


@router.get("/notion/status", response_model=NotionExportStatusResponse)
async def get_notion_export_status(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> NotionExportStatusResponse:
    """Check Notion export status for a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    exported = project.notion_page_id is not None
    notion_url = None
    if exported and project.notion_page_id:
        page_id = project.notion_page_id.replace("-", "")
        notion_url = f"https://notion.so/{page_id}"

    return NotionExportStatusResponse(
        exported=exported,
        notion_page_id=project.notion_page_id,
        notion_url=notion_url,
    )
