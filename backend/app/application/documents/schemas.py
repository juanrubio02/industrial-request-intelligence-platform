from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.documents.statuses import DocumentProcessingStatus


class DocumentReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    request_id: UUID
    organization_id: UUID
    uploaded_by_membership_id: UUID
    original_filename: str
    storage_key: str
    content_type: str
    size_bytes: int
    processing_status: DocumentProcessingStatus
    verified_structured_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class DocumentProcessingEnqueuedReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: UUID
    processing_status: DocumentProcessingStatus
