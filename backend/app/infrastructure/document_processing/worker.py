import logging
import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.documents.processing import DocumentProcessor
from app.application.documents.schemas import DocumentReadModel
from app.application.documents.services import ProcessDocumentUseCase
from app.domain.document_processing_jobs.entities import DocumentProcessingJob
from app.domain.documents.statuses import DocumentProcessingStatus
from app.infrastructure.document_processing_jobs.repositories import (
    SqlAlchemyDocumentProcessingJobRepository,
)
from app.infrastructure.document_processing_results.repositories import (
    SqlAlchemyDocumentProcessingResultRepository,
)
from app.infrastructure.documents.repositories import SqlAlchemyDocumentRepository
from app.infrastructure.organization_memberships.repositories import (
    SqlAlchemyOrganizationMembershipRepository,
)
from app.interfaces.http.logging import bind_log_context, log_event, reset_log_context


class DocumentProcessingWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        document_processor: DocumentProcessor,
    ) -> None:
        self._session_factory = session_factory
        self._document_processor = document_processor

    async def process(self, document_id: UUID) -> DocumentReadModel:
        async with self._session_factory() as session:
            document_repository = SqlAlchemyDocumentRepository(session=session)
            membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
            document_processing_result_repository = SqlAlchemyDocumentProcessingResultRepository(
                session=session
            )
            started_at = time.perf_counter()
            current_document = await document_repository.get_by_id(document_id)
            membership = (
                await membership_repository.get_by_id(current_document.uploaded_by_membership_id)
                if current_document is not None
                else None
            )
            log_event(
                logging.INFO,
                {
                    "event": "document_processing_started",
                    "document_id": str(document_id),
                    "organization_id": (
                        None if current_document is None else str(current_document.organization_id)
                    ),
                    "membership_id": (
                        None
                        if current_document is None
                        else str(current_document.uploaded_by_membership_id)
                    ),
                    "user_id": None if membership is None else str(membership.user_id),
                    "status_code": 202,
                    "latency_ms": 0.0,
                },
            )
            use_case = ProcessDocumentUseCase(
                document_repository=document_repository,
                document_processing_result_repository=document_processing_result_repository,
                document_processor=self._document_processor,
            )
            try:
                processed_document = await use_case.execute(document_id)
            except Exception as exc:
                log_event(
                    logging.ERROR,
                    {
                        "event": "document_processing_failed",
                        "document_id": str(document_id),
                        "organization_id": (
                            None if current_document is None else str(current_document.organization_id)
                        ),
                        "membership_id": (
                            None
                            if current_document is None
                            else str(current_document.uploaded_by_membership_id)
                        ),
                        "user_id": None if membership is None else str(membership.user_id),
                        "status_code": 500,
                        "latency_ms": round((time.perf_counter() - started_at) * 1000, 3),
                        "error_type": exc.__class__.__name__,
                    },
                )
                raise

            self._log_completion_event(
                processed_document=processed_document,
                user_id=None if membership is None else str(membership.user_id),
                started_at=started_at,
            )
            return processed_document

    async def process_job(self, job: DocumentProcessingJob) -> DocumentReadModel:
        context_tokens = bind_log_context(
            job_id=str(job.id),
            organization_id=str(job.organization_id),
        )
        try:
            processed_document = await self.process(job.document_id)
        except Exception:
            await self._mark_job_failed(job.id)
            raise
        finally:
            reset_log_context(context_tokens)

        if processed_document.processing_status == DocumentProcessingStatus.FAILED:
            await self._mark_job_failed(job.id)
        else:
            await self._mark_job_completed(job.id)
        return processed_document

    async def process_next_job(self) -> DocumentProcessingJob | None:
        job = await self._claim_next_job()
        if job is None:
            return None

        await self.process_job(job)
        return job

    async def run_once(self) -> bool:
        return await self.process_next_job() is not None

    async def _claim_next_job(self) -> DocumentProcessingJob | None:
        async with self._session_factory() as session:
            job_repository = SqlAlchemyDocumentProcessingJobRepository(session=session)
            job = await job_repository.get_next_pending_job()
            if job is None:
                return None
            await job_repository.save_changes()
            return job

    async def _mark_job_completed(self, job_id: UUID) -> None:
        async with self._session_factory() as session:
            job_repository = SqlAlchemyDocumentProcessingJobRepository(session=session)
            await job_repository.mark_completed(job_id)
            await job_repository.save_changes()

    async def _mark_job_failed(self, job_id: UUID) -> None:
        async with self._session_factory() as session:
            job_repository = SqlAlchemyDocumentProcessingJobRepository(session=session)
            await job_repository.mark_failed(job_id)
            await job_repository.save_changes()

    def _log_completion_event(
        self,
        *,
        processed_document: DocumentReadModel,
        user_id: str | None,
        started_at: float,
    ) -> None:
        if processed_document.processing_status == DocumentProcessingStatus.FAILED:
            log_event(
                logging.ERROR,
                {
                    "event": "document_processing_failed",
                    "document_id": str(processed_document.id),
                    "organization_id": str(processed_document.organization_id),
                    "membership_id": str(processed_document.uploaded_by_membership_id),
                    "user_id": user_id,
                    "status_code": 500,
                    "latency_ms": round((time.perf_counter() - started_at) * 1000, 3),
                    "error_type": "DocumentProcessingFailed",
                },
            )
            return

        log_event(
            logging.INFO,
            {
                "event": "document_processing_completed",
                "document_id": str(processed_document.id),
                "organization_id": str(processed_document.organization_id),
                "membership_id": str(processed_document.uploaded_by_membership_id),
                "user_id": user_id,
                "status_code": 200,
                "latency_ms": round((time.perf_counter() - started_at) * 1000, 3),
                "error_type": None,
            },
        )
