import logging
from uuid import UUID

from app.application.documents.processing import DocumentProcessingDispatcher
from app.domain.document_processing_jobs.repositories import DocumentProcessingJobRepository
from app.interfaces.http.logging import bind_log_context
from app.interfaces.http.logging import log_event
from app.interfaces.http.logging import reset_log_context


class DatabaseDocumentProcessingDispatcher(DocumentProcessingDispatcher):
    def __init__(self, job_repository: DocumentProcessingJobRepository) -> None:
        self._job_repository = job_repository

    async def enqueue(self, document_id: UUID, organization_id: UUID) -> None:
        active_job = await self._job_repository.get_active_by_document_id(document_id)
        if active_job is not None:
            return None

        job = await self._job_repository.create_job(
            document_id=document_id,
            organization_id=organization_id,
        )
        context_tokens = bind_log_context(job_id=str(job.id))
        try:
            log_event(
                logging.INFO,
                {
                    "event": "document_processing_job_enqueued",
                    "document_id": str(document_id),
                    "organization_id": str(organization_id),
                    "job_id": str(job.id),
                    "status_code": 202,
                },
            )
        finally:
            reset_log_context(context_tokens)


AsyncioDocumentProcessingDispatcher = DatabaseDocumentProcessingDispatcher
