from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.documents.statuses import DocumentProcessingStatus


@dataclass(frozen=True, slots=True)
class Document:
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
