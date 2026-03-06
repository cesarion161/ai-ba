"""Graph editing endpoints for pre-execution modifications."""

from __future__ import annotations

import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.graph_edit import AddEdgeRequest, AddNodeRequest, UpdateNodeConfigRequest
from app.api.schemas.node import NodeResponse
from app.models.database import get_db
from app.models.workflow_node import NodeEdge, NodeStatus, NodeType, WorkflowNode
from app.services import project_service

router = APIRouter(prefix="/api/projects/{project_id}/graph", tags=["graph-edit"])


async def _get_project_or_404(db: AsyncSession, project_id: uuid.UUID):  # type: ignore[no-untyped-def]
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _get_node_by_slug(
    db: AsyncSession, project_id: uuid.UUID, slug: str
) -> WorkflowNode:
    result = await db.execute(
        select(WorkflowNode).where(
            WorkflowNode.project_id == project_id, WorkflowNode.slug == slug
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{slug}' not found")
    return node


def _detect_cycle(nodes: list[WorkflowNode], edges: list[NodeEdge]) -> bool:
    """Return True if there's a cycle."""
    id_to_slug = {n.id: n.slug for n in nodes}
    in_degree: dict[str, int] = defaultdict(int)
    adj: dict[str, list[str]] = defaultdict(list)
    slugs = set(id_to_slug.values())
    for s in slugs:
        in_degree.setdefault(s, 0)
    for e in edges:
        f = id_to_slug.get(e.from_node_id)
        t = id_to_slug.get(e.to_node_id)
        if f and t:
            adj[f].append(t)
            in_degree[t] += 1

    queue = [s for s, d in in_degree.items() if d == 0]
    visited = 0
    while queue:
        current = queue.pop(0)
        visited += 1
        for neighbor in adj[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return visited != len(slugs)


@router.post("/nodes", response_model=NodeResponse, status_code=201)
async def add_node(
    project_id: uuid.UUID,
    body: AddNodeRequest,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    await _get_project_or_404(db, project_id)

    # Check slug uniqueness
    existing = await db.execute(
        select(WorkflowNode).where(
            WorkflowNode.project_id == project_id, WorkflowNode.slug == body.slug
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Node '{body.slug}' already exists")

    try:
        node_type = NodeType(body.node_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid node_type: {body.node_type}")

    node = WorkflowNode(
        project_id=project_id,
        slug=body.slug,
        label=body.label,
        branch=body.branch,
        node_type=node_type,
        status=NodeStatus.PENDING,
        requires_approval=body.requires_approval,
        config=body.config,
    )
    db.add(node)
    await db.flush()

    # Create edges for dependencies
    for dep_slug in body.depends_on:
        dep_node = await _get_node_by_slug(db, project_id, dep_slug)
        edge = NodeEdge(from_node_id=dep_node.id, to_node_id=node.id)
        db.add(edge)

    # If no deps, mark as READY
    if not body.depends_on:
        node.status = NodeStatus.READY

    await db.commit()
    await db.refresh(node)
    return NodeResponse.model_validate(node)


@router.put("/nodes/{slug}", response_model=NodeResponse)
async def update_node_config(
    project_id: uuid.UUID,
    slug: str,
    body: UpdateNodeConfigRequest,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    await _get_project_or_404(db, project_id)
    node = await _get_node_by_slug(db, project_id, slug)

    if node.status not in (NodeStatus.PENDING, NodeStatus.READY):
        raise HTTPException(status_code=400, detail="Can only edit pending/ready nodes")

    if body.label is not None:
        node.label = body.label
    if body.config is not None:
        node.config = body.config
    if body.requires_approval is not None:
        node.requires_approval = body.requires_approval

    await db.commit()
    await db.refresh(node)
    return NodeResponse.model_validate(node)


@router.delete("/nodes/{slug}", status_code=204)
async def delete_node(
    project_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_project_or_404(db, project_id)
    node = await _get_node_by_slug(db, project_id, slug)

    if node.status not in (NodeStatus.PENDING, NodeStatus.READY):
        raise HTTPException(status_code=400, detail="Can only delete pending/ready nodes")

    await db.delete(node)
    await db.commit()


@router.post("/edges", status_code=201)
async def add_edge(
    project_id: uuid.UUID,
    body: AddEdgeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _get_project_or_404(db, project_id)
    from_node = await _get_node_by_slug(db, project_id, body.from_slug)
    to_node = await _get_node_by_slug(db, project_id, body.to_slug)

    # Check for duplicate
    existing = await db.execute(
        select(NodeEdge).where(
            NodeEdge.from_node_id == from_node.id, NodeEdge.to_node_id == to_node.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Edge already exists")

    edge = NodeEdge(from_node_id=from_node.id, to_node_id=to_node.id)
    db.add(edge)
    await db.flush()

    # Check for cycles
    nodes, edges = await project_service.get_project_graph(db, project_id)
    if _detect_cycle(nodes, edges):
        await db.rollback()
        raise HTTPException(status_code=400, detail="Adding this edge would create a cycle")

    await db.commit()
    return {"from_slug": body.from_slug, "to_slug": body.to_slug}


@router.delete("/edges", status_code=204)
async def delete_edge(
    project_id: uuid.UUID,
    from_slug: str,
    to_slug: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_project_or_404(db, project_id)
    from_node = await _get_node_by_slug(db, project_id, from_slug)
    to_node = await _get_node_by_slug(db, project_id, to_slug)

    result = await db.execute(
        select(NodeEdge).where(
            NodeEdge.from_node_id == from_node.id, NodeEdge.to_node_id == to_node.id
        )
    )
    edge = result.scalar_one_or_none()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")

    await db.delete(edge)
    await db.commit()
