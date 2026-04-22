from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.document_processing_jobs.statuses import DocumentProcessingJobStatus


@dataclass(frozen=True, slots=True)
class DocumentProcessingJob:
    id: UUID
    document_id: UUID
    organization_id: UUID
    status: DocumentProcessingJobStatus
    attempts: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime
    locked_at: datetime | None = None
