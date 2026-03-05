from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NodeResponse(BaseModel):
    id: uuid.UUID
    slug: str
    label: str
    branch: str
    node_type: str
    status: str
    requires_approval: bool
    config: dict | None
    input_data: dict | None
    output_data: dict | None
    user_feedback: str | None
    retry_count: int
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class NodeListResponse(BaseModel):
    nodes: list[NodeResponse]


class RejectRequest(BaseModel):
    feedback: str = Field(..., min_length=1)


class OutputEditRequest(BaseModel):
    output_data: dict


class AnswerRequest(BaseModel):
    answers: dict
