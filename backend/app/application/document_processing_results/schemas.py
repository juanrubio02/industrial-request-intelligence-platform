from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.document_processing_results.document_types import (
    DocumentDetectedType,
)
from app.domain.document_processing_results.statuses import (
    DocumentProcessingResultStatus,
)


class DocumentProcessingResultReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    document_id: UUID
    organization_id: UUID
    status: DocumentProcessingResultStatus
    extracted_text: str | None
    summary: str | None
    detected_document_type: DocumentDetectedType | None
    structured_data: dict[str, Any] | None
    error_message: str | None
    processed_at: datetime
    created_at: datetime
    updated_at: datetime
