from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentTypeResponse(BaseModel):
    id: uuid.UUID
    key: str
    label: str
    description: str
    category: str
    default_dependencies: list[str] | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentTypeListResponse(BaseModel):
    document_types: list[DocumentTypeResponse]
