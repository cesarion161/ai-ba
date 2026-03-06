from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    template_key: str = "market_research"


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    template_key: str
    status: str
    chat_phase: str | None = None
    selected_doc_types: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
