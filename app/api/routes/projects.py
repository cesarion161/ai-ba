from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse
from app.models.database import get_db
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Placeholder user ID until auth is implemented
PLACEHOLDER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    try:
        project = await project_service.create_project(
            db, PLACEHOLDER_USER_ID, body.name, body.description, body.template_key
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ProjectResponse.model_validate(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    projects = await project_service.list_projects(db, PLACEHOLDER_USER_ID)
    return ProjectListResponse(projects=[ProjectResponse.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await project_service.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
