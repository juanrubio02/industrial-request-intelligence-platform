from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.document_processing_jobs.entities import DocumentProcessingJob


class DocumentProcessingJobRepository(ABC):
    @abstractmethod
    async def create_job(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
        max_attempts: int = 3,
    ) -> DocumentProcessingJob:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> DocumentProcessingJob | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentProcessingJob | None:
        raise NotImplementedError

    @abstractmethod
    async def get_next_pending_job(self) -> DocumentProcessingJob | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_completed(self, job_id: UUID) -> DocumentProcessingJob:
        raise NotImplementedError

    @abstractmethod
    async def mark_failed(self, job_id: UUID) -> DocumentProcessingJob:
        raise NotImplementedError

    @abstractmethod
    async def save_changes(self) -> None:
        raise NotImplementedError
