from __future__ import annotations

from pydantic import BaseModel, Field


class AddNodeRequest(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=255)
    branch: str = Field(default="custom", max_length=100)
    node_type: str
    requires_approval: bool = True
    config: dict | None = None
    depends_on: list[str] = []


class UpdateNodeConfigRequest(BaseModel):
    label: str | None = None
    config: dict | None = None
    requires_approval: bool | None = None


class AddEdgeRequest(BaseModel):
    from_slug: str
    to_slug: str
