from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import NodeArtifact
from app.models.database import get_db
from app.models.workflow_node import WorkflowNode

router = APIRouter(prefix="/api/projects/{project_id}/artifacts", tags=["artifacts"])


class ArtifactResponse(BaseModel):
    id: uuid.UUID
    node_id: uuid.UUID
    artifact_type: str
    title: str
    content: str | None
    version: int
    s3_key: str | None

    model_config = {"from_attributes": True}


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactResponse]


class ImportResult(BaseModel):
    imported: int
    artifacts: list[ArtifactResponse]


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ArtifactListResponse:
    result = await db.execute(
        select(NodeArtifact)
        .join(WorkflowNode)
        .where(WorkflowNode.project_id == project_id)
        .order_by(NodeArtifact.created_at.desc())
    )
    artifacts = result.scalars().all()
    return ArtifactListResponse(
        artifacts=[ArtifactResponse.model_validate(a) for a in artifacts]
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    project_id: uuid.UUID,
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ArtifactResponse:
    artifact = await db.get(NodeArtifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return ArtifactResponse.model_validate(artifact)


@router.get("/node/{slug}", response_model=ArtifactListResponse)
async def list_node_artifacts(
    project_id: uuid.UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> ArtifactListResponse:
    result = await db.execute(
        select(NodeArtifact)
        .join(WorkflowNode)
        .where(
            WorkflowNode.project_id == project_id,
            WorkflowNode.slug == slug,
        )
        .order_by(NodeArtifact.version.desc())
    )
    artifacts = result.scalars().all()
    return ArtifactListResponse(
        artifacts=[ArtifactResponse.model_validate(a) for a in artifacts]
    )


@router.post("/import", response_model=ImportResult, status_code=201)
async def import_artifacts(
    project_id: uuid.UUID,
    node_slug: str,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
) -> ImportResult:
    """Upload .md files and create node artifacts."""
    # Verify the node exists
    result = await db.execute(
        select(WorkflowNode).where(
            WorkflowNode.project_id == project_id,
            WorkflowNode.slug == node_slug,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_slug}' not found")

    # Get current max version for this node
    max_ver_result = await db.execute(
        select(func.coalesce(func.max(NodeArtifact.version), 0)).where(
            NodeArtifact.node_id == node.id
        )
    )
    max_version = max_ver_result.scalar() or 0

    created: list[NodeArtifact] = []
    for i, file in enumerate(files):
        if not file.filename or not file.filename.endswith(".md"):
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' is not a .md file",
            )

        content_bytes = await file.read()
        content = content_bytes.decode("utf-8")
        title = file.filename.removesuffix(".md").replace("_", " ").replace("-", " ").title()

        artifact = NodeArtifact(
            node_id=node.id,
            artifact_type="document",
            title=title,
            content=content,
            version=max_version + i + 1,
        )
        db.add(artifact)
        created.append(artifact)

    await db.commit()
    for a in created:
        await db.refresh(a)

    return ImportResult(
        imported=len(created),
        artifacts=[ArtifactResponse.model_validate(a) for a in created],
    )
