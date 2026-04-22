from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.document_processing_jobs.entities import DocumentProcessingJob
from app.domain.document_processing_jobs.repositories import (
    DocumentProcessingJobRepository,
)
from app.domain.document_processing_jobs.statuses import DocumentProcessingJobStatus
from app.infrastructure.database.models.document_processing_job import (
    DocumentProcessingJobModel,
)


class SqlAlchemyDocumentProcessingJobRepository(DocumentProcessingJobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
        max_attempts: int = 3,
    ) -> DocumentProcessingJob:
        now = datetime.now(UTC)
        job = DocumentProcessingJob(
            id=uuid4(),
            document_id=document_id,
            organization_id=organization_id,
            status=DocumentProcessingJobStatus.PENDING,
            attempts=0,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
            locked_at=None,
        )
        self._session.add(self._to_model(job))
        return job

    async def get_by_id(self, job_id: UUID) -> DocumentProcessingJob | None:
        model = await self._session.get(DocumentProcessingJobModel, job_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def get_active_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentProcessingJob | None:
        result = await self._session.execute(
            select(DocumentProcessingJobModel)
            .where(
                DocumentProcessingJobModel.document_id == document_id,
                DocumentProcessingJobModel.status.in_(
                    (
                        DocumentProcessingJobStatus.PENDING,
                        DocumentProcessingJobStatus.PROCESSING,
                    )
                ),
            )
            .order_by(
                DocumentProcessingJobModel.created_at.desc(),
                DocumentProcessingJobModel.id.desc(),
            )
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def get_next_pending_job(self) -> DocumentProcessingJob | None:
        result = await self._session.execute(
            select(DocumentProcessingJobModel)
            .where(
                DocumentProcessingJobModel.status == DocumentProcessingJobStatus.PENDING,
                DocumentProcessingJobModel.attempts < DocumentProcessingJobModel.max_attempts,
            )
            .order_by(
                DocumentProcessingJobModel.created_at.asc(),
                DocumentProcessingJobModel.id.asc(),
            )
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        now = datetime.now(UTC)
        model.status = DocumentProcessingJobStatus.PROCESSING
        model.attempts += 1
        model.locked_at = now
        model.updated_at = now
        return self._to_domain(model)

    async def mark_completed(self, job_id: UUID) -> DocumentProcessingJob:
        model = await self._session.get(DocumentProcessingJobModel, job_id)
        if model is None:
            raise ValueError(f"Document processing job '{job_id}' was not found.")

        now = datetime.now(UTC)
        model.status = DocumentProcessingJobStatus.COMPLETED
        model.locked_at = None
        model.updated_at = now
        return self._to_domain(model)

    async def mark_failed(self, job_id: UUID) -> DocumentProcessingJob:
        model = await self._session.get(DocumentProcessingJobModel, job_id)
        if model is None:
            raise ValueError(f"Document processing job '{job_id}' was not found.")

        now = datetime.now(UTC)
        model.status = DocumentProcessingJobStatus.FAILED
        model.locked_at = None
        model.updated_at = now
        return self._to_domain(model)

    async def save_changes(self) -> None:
        await self._session.commit()

    @staticmethod
    def _to_domain(model: DocumentProcessingJobModel) -> DocumentProcessingJob:
        return DocumentProcessingJob(
            id=model.id,
            document_id=model.document_id,
            organization_id=model.organization_id,
            status=model.status,
            attempts=model.attempts,
            max_attempts=model.max_attempts,
            created_at=model.created_at,
            updated_at=model.updated_at,
            locked_at=model.locked_at,
        )

    @staticmethod
    def _to_model(job: DocumentProcessingJob) -> DocumentProcessingJobModel:
        return DocumentProcessingJobModel(
            id=job.id,
            document_id=job.document_id,
            organization_id=job.organization_id,
            status=job.status,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            created_at=job.created_at,
            updated_at=job.updated_at,
            locked_at=job.locked_at,
        )
