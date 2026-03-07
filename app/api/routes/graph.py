from __future__ import annotations

import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.graph import (
    BranchGroup,
    EdgeResponse,
    GraphResponse,
    GraphStatusResponse,
    NodeSummary,
)
from app.models.database import get_db
from app.services import project_service
from app.tasks.workflow_tasks import run_workflow_task

router = APIRouter(prefix="/api/projects/{project_id}/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
async def get_graph(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> GraphResponse:
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes, edges = await project_service.get_project_graph(db, project_id)

    slug_by_id = {n.id: n.slug for n in nodes}

    return GraphResponse(
        project_id=project_id,
        nodes=[
            NodeSummary(
                slug=n.slug,
                label=n.label,
                branch=n.branch,
                node_type=n.node_type.value,
                status=n.status.value,
                requires_approval=n.requires_approval,
            )
            for n in nodes
        ],
        edges=[
            EdgeResponse(
                from_slug=slug_by_id[e.from_node_id],
                to_slug=slug_by_id[e.to_node_id],
            )
            for e in edges
        ],
    )


@router.get("/preflight")
async def preflight_check(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check if the graph can be run — validates required API keys for node types."""
    from app.core.config import get_settings

    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes, _ = await project_service.get_project_graph(db, project_id)
    node_types = {n.node_type.value for n in nodes}

    settings = get_settings()
    issues: list[str] = []

    # Research nodes need Tavily
    if "research" in node_types and not settings.TAVILY_API_KEY:
        issues.append("Research nodes require TAVILY_API_KEY. Set it in .env or remove research nodes.")

    # Calculate nodes need E2B for sandbox execution
    if "calculate" in node_types and not settings.E2B_API_KEY:
        issues.append("Calculate nodes require E2B_API_KEY for secure code execution. Set it in .env or remove calculate nodes.")

    # LLM key needed for everything
    has_llm_key = bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY or settings.GOOGLE_API_KEY)
    if not has_llm_key:
        issues.append("No LLM API key configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY.")

    return {
        "can_run": len(issues) == 0,
        "issues": issues,
        "node_types": sorted(node_types),
    }


@router.post("/run")
async def run_graph(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.chat_phase == "executing":
        raise HTTPException(status_code=409, detail="Workflow is already running")

    project.chat_phase = "executing"
    await db.commit()

    task = run_workflow_task.delay(str(project_id))
    return {"task_id": task.id, "status": "started"}


@router.get("/status", response_model=GraphStatusResponse)
async def get_graph_status(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> GraphStatusResponse:
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes, _ = await project_service.get_project_graph(db, project_id)

    by_status: dict[str, int] = defaultdict(int)
    branches_map: dict[str, list[NodeSummary]] = defaultdict(list)
    done_count = 0

    for n in nodes:
        by_status[n.status.value] += 1
        branches_map[n.branch].append(
            NodeSummary(
                slug=n.slug,
                label=n.label,
                branch=n.branch,
                node_type=n.node_type.value,
                status=n.status.value,
                requires_approval=n.requires_approval,
            )
        )
        if n.status.value in ("approved", "skipped"):
            done_count += 1

    total = len(nodes)
    progress = (done_count / total * 100) if total > 0 else 0.0

    return GraphStatusResponse(
        project_id=project_id,
        total_nodes=total,
        by_status=dict(by_status),
        branches=[BranchGroup(branch=b, nodes=ns) for b, ns in branches_map.items()],
        progress_pct=round(progress, 1),
    )
