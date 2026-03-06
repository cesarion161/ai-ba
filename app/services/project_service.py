from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.instantiate import instantiate_workflow
from app.engine.templates.registry import get_template
from app.models.project import Project
from app.models.workflow_node import NodeEdge, WorkflowNode
from app.services import audit_service


async def create_project(
    session: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    description: str | None,
    template_key: str,
) -> Project:
    template = get_template(template_key)
    project = Project(
        user_id=user_id,
        name=name,
        description=description,
        template_key=template_key,
    )
    session.add(project)
    await session.flush()

    await instantiate_workflow(session, project.id, template)
    await audit_service.record(
        session, "create", "project", entity_id=project.id,
        project_id=project.id, user_id=user_id,
    )
    await session.commit()
    await session.refresh(project)
    return project


async def get_project(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    return await session.get(Project, project_id)


async def list_projects(session: AsyncSession, user_id: uuid.UUID) -> list[Project]:
    result = await session.execute(
        select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_project(session: AsyncSession, project_id: uuid.UUID) -> bool:
    project = await session.get(Project, project_id)
    if not project:
        return False
    await audit_service.record(
        session, "delete", "project", entity_id=project_id, project_id=project_id,
    )
    await session.delete(project)
    await session.commit()
    return True


async def get_project_graph(
    session: AsyncSession, project_id: uuid.UUID
) -> tuple[list[WorkflowNode], list[NodeEdge]]:
    nodes_result = await session.execute(
        select(WorkflowNode).where(WorkflowNode.project_id == project_id)
    )
    nodes = list(nodes_result.scalars().all())

    node_ids = [n.id for n in nodes]
    edges_result = await session.execute(
        select(NodeEdge).where(NodeEdge.from_node_id.in_(node_ids))
    )
    edges = list(edges_result.scalars().all())

    return nodes, edges
