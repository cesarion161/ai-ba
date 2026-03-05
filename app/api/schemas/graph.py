from __future__ import annotations

import uuid

from pydantic import BaseModel


class EdgeResponse(BaseModel):
    from_slug: str
    to_slug: str


class NodeSummary(BaseModel):
    slug: str
    label: str
    branch: str
    node_type: str
    status: str
    requires_approval: bool

    model_config = {"from_attributes": True}


class GraphResponse(BaseModel):
    project_id: uuid.UUID
    nodes: list[NodeSummary]
    edges: list[EdgeResponse]


class BranchGroup(BaseModel):
    branch: str
    nodes: list[NodeSummary]


class GraphStatusResponse(BaseModel):
    project_id: uuid.UUID
    total_nodes: int
    by_status: dict[str, int]
    branches: list[BranchGroup]
    progress_pct: float
