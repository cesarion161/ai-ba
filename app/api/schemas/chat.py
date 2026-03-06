from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    role: str
    content: str
    metadata_: dict | None = Field(None, alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    total: int
    has_more: bool


class DocumentSelectionRequest(BaseModel):
    doc_type_keys: list[str] = Field(..., min_length=1)


class ProjectFromChatRequest(BaseModel):
    initial_prompt: str = Field(..., min_length=1)
    name: str | None = None
