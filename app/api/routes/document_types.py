from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.document_type import DocumentTypeListResponse, DocumentTypeResponse
from app.models.database import get_db
from app.services import document_type_service

router = APIRouter(prefix="/api/document-types", tags=["document-types"])


@router.get("", response_model=DocumentTypeListResponse)
async def list_document_types(
    db: AsyncSession = Depends(get_db),
) -> DocumentTypeListResponse:
    doc_types = await document_type_service.list_document_types(db)
    return DocumentTypeListResponse(
        document_types=[DocumentTypeResponse.model_validate(dt) for dt in doc_types]
    )
