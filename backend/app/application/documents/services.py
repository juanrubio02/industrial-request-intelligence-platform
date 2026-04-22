from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.common.pagination import PaginatedResult, PaginationParams
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipNotFoundError,
)
from app.application.documents.commands import CreateDocumentCommand
from app.application.documents.commands import EnqueueDocumentProcessingCommand
from app.application.documents.commands import UpdateDocumentVerifiedDataCommand
from app.application.documents.commands import UploadDocumentCommand
from app.application.documents.exceptions import (
    DocumentOrganizationMismatchError,
    DocumentMembershipOrganizationMismatchError,
    DocumentNotFoundError,
    DocumentRequestOrganizationMismatchError,
    DocumentUploadInvalidFileError,
    InvalidDocumentProcessingStatusTransitionError,
)
from app.application.documents.processing import DocumentProcessingDispatcher
from app.application.documents.processing import DocumentProcessingOutput
from app.application.documents.processing import DocumentProcessor
from app.application.documents.schemas import DocumentProcessingEnqueuedReadModel
from app.application.documents.schemas import DocumentReadModel
from app.application.documents.storage import DocumentStorage, generate_storage_key
from app.domain.document_processing_results.entities import DocumentProcessingResult
from app.domain.document_processing_results.repositories import (
    DocumentProcessingResultRepository,
)
from app.domain.document_processing_results.statuses import (
    DocumentProcessingResultStatus,
)
from app.application.requests.exceptions import RequestNotFoundError
from app.domain.documents.entities import Document
from app.domain.documents.repositories import DocumentRepository
from app.domain.documents.statuses import DocumentProcessingStatus
from app.domain.documents.transitions import is_valid_document_processing_status_transition
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.domain.requests.repositories import RequestRepository


class CreateDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepository,
        request_repository: RequestRepository,
        organization_membership_repository: OrganizationMembershipRepository,
        request_activity_repository: RequestActivityRepository,
    ) -> None:
        self._document_repository = document_repository
        self._request_repository = request_repository
        self._organization_membership_repository = organization_membership_repository
        self._request_activity_repository = request_activity_repository

    async def execute(self, command: CreateDocumentCommand) -> DocumentReadModel:
        request = await self._request_repository.get_by_id(command.request_id)
        if request is None:
            raise RequestNotFoundError(f"Request '{command.request_id}' was not found.")

        if request.organization_id != command.organization_id:
            raise DocumentRequestOrganizationMismatchError(
                "The provided request does not belong to the provided organization."
            )

        membership = await self._organization_membership_repository.get_by_id(
            command.uploaded_by_membership_id
        )
        if membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{command.uploaded_by_membership_id}' was not found."
            )

        if membership.organization_id != command.organization_id:
            raise DocumentMembershipOrganizationMismatchError(
                "The provided membership does not belong to the provided organization."
            )

        now = datetime.now(UTC)
        storage_key = command.storage_key or generate_storage_key(command.original_filename)
        document = Document(
            id=uuid4(),
            request_id=command.request_id,
            organization_id=command.organization_id,
            uploaded_by_membership_id=command.uploaded_by_membership_id,
            original_filename=command.original_filename,
            storage_key=storage_key,
            content_type=command.content_type,
            size_bytes=command.size_bytes,
            processing_status=DocumentProcessingStatus.PENDING,
            verified_structured_data=None,
            created_at=now,
            updated_at=now,
        )
        created_document = await self._document_repository.add(document)
        await self._request_activity_repository.add(
            RequestActivity(
                id=uuid4(),
                request_id=created_document.request_id,
                organization_id=created_document.organization_id,
                membership_id=created_document.uploaded_by_membership_id,
                type=RequestActivityType.DOCUMENT_UPLOADED,
                payload={
                    "document_id": str(created_document.id),
                    "storage_key": created_document.storage_key,
                    "original_filename": created_document.original_filename,
                    "content_type": created_document.content_type,
                    "size_bytes": created_document.size_bytes,
                    "processing_status": created_document.processing_status.value,
                },
                created_at=now,
            )
        )
        await self._document_repository.save_changes()
        return DocumentReadModel.model_validate(created_document, from_attributes=True)


class UploadDocumentUseCase:
    def __init__(
        self,
        document_storage: DocumentStorage,
        create_document_use_case: CreateDocumentUseCase,
    ) -> None:
        self._document_storage = document_storage
        self._create_document_use_case = create_document_use_case

    async def execute(self, command: UploadDocumentCommand) -> DocumentReadModel:
        if not command.original_filename.strip():
            raise DocumentUploadInvalidFileError("Uploaded file must include a filename.")

        if len(command.content) == 0:
            raise DocumentUploadInvalidFileError("Uploaded file cannot be empty.")

        content_type = command.content_type or "application/octet-stream"
        storage_key = generate_storage_key(command.original_filename)

        await self._document_storage.save(
            storage_key=storage_key,
            content=command.content,
            content_type=content_type,
        )

        try:
            return await self._create_document_use_case.execute(
                CreateDocumentCommand(
                    request_id=command.request_id,
                    organization_id=command.organization_id,
                    uploaded_by_membership_id=command.uploaded_by_membership_id,
                    original_filename=command.original_filename,
                    storage_key=storage_key,
                    content_type=content_type,
                    size_bytes=len(command.content),
                )
            )
        except Exception:
            await self._document_storage.delete(storage_key=storage_key)
            raise


class GetDocumentByIdUseCase:
    def __init__(self, document_repository: DocumentRepository) -> None:
        self._document_repository = document_repository

    async def execute(self, document_id: UUID, organization_id: UUID) -> DocumentReadModel:
        document = await self._document_repository.get_by_id(document_id)
        if document is None or document.organization_id != organization_id:
            raise DocumentNotFoundError(f"Document '{document_id}' was not found.")

        return DocumentReadModel.model_validate(document, from_attributes=True)


class ListRequestDocumentsUseCase:
    def __init__(
        self,
        document_repository: DocumentRepository,
        request_repository: RequestRepository,
    ) -> None:
        self._document_repository = document_repository
        self._request_repository = request_repository

    async def execute(
        self,
        request_id: UUID,
        organization_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResult[DocumentReadModel]:
        request = await self._request_repository.get_by_id(request_id)
        if request is None or request.organization_id != organization_id:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        documents = await self._document_repository.list_by_request_id(
            request_id,
            organization_id=organization_id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        total = await self._document_repository.count_by_request_id(
            request_id,
            organization_id=organization_id,
        )
        return PaginatedResult(
            items=[
                DocumentReadModel.model_validate(document, from_attributes=True)
                for document in documents
            ],
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )


class EnqueueDocumentProcessingUseCase:
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_processing_dispatcher: DocumentProcessingDispatcher,
    ) -> None:
        self._document_repository = document_repository
        self._document_processing_dispatcher = document_processing_dispatcher

    async def execute(
        self,
        command: EnqueueDocumentProcessingCommand,
    ) -> DocumentProcessingEnqueuedReadModel:
        document = await self._document_repository.get_by_id(command.document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document '{command.document_id}' was not found.")

        if document.organization_id != command.organization_id:
            raise DocumentOrganizationMismatchError(
                "The provided document does not belong to the provided organization."
            )

        if document.processing_status in {
            DocumentProcessingStatus.PROCESSING,
            DocumentProcessingStatus.PROCESSED,
        }:
            return DocumentProcessingEnqueuedReadModel(
                document_id=document.id,
                processing_status=document.processing_status,
            )

        if document.processing_status is DocumentProcessingStatus.FAILED:
            if not is_valid_document_processing_status_transition(
                document.processing_status,
                DocumentProcessingStatus.PENDING,
            ):
                raise InvalidDocumentProcessingStatusTransitionError(
                    "Cannot reset failed document back to 'PENDING' for reprocessing."
                )
            document = await self._document_repository.update_processing_status(
                document_id=document.id,
                new_status=DocumentProcessingStatus.PENDING,
                updated_at=datetime.now(UTC),
            )

        await self._document_processing_dispatcher.enqueue(
            document.id,
            document.organization_id,
        )
        await self._document_repository.save_changes()
        return DocumentProcessingEnqueuedReadModel(
            document_id=document.id,
            processing_status=document.processing_status,
        )


class UpdateDocumentVerifiedDataUseCase:
    def __init__(
        self,
        document_repository: DocumentRepository,
        request_activity_repository: RequestActivityRepository,
    ) -> None:
        self._document_repository = document_repository
        self._request_activity_repository = request_activity_repository

    async def execute(
        self,
        command: UpdateDocumentVerifiedDataCommand,
    ) -> DocumentReadModel:
        document = await self._document_repository.get_by_id(command.document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document '{command.document_id}' was not found.")

        if document.organization_id != command.organization_id:
            raise DocumentNotFoundError(f"Document '{command.document_id}' was not found.")

        now = datetime.now(UTC)
        sanitized_data = self._sanitize_verified_structured_data(
            command.verified_structured_data
        )
        updated_document = await self._document_repository.update_verified_structured_data(
            command.document_id,
            sanitized_data,
            now,
        )
        await self._request_activity_repository.add(
            RequestActivity(
                id=uuid4(),
                request_id=updated_document.request_id,
                organization_id=updated_document.organization_id,
                membership_id=command.membership_id,
                type=RequestActivityType.DOCUMENT_VERIFIED_DATA_UPDATED,
                payload={
                    "document_id": str(updated_document.id),
                    "verified_structured_data": sanitized_data or {},
                },
                created_at=now,
            )
        )
        await self._document_repository.save_changes()
        return DocumentReadModel.model_validate(updated_document, from_attributes=True)

    @staticmethod
    def _sanitize_verified_structured_data(
        verified_structured_data: dict[str, Any],
    ) -> dict[str, str] | None:
        sanitized = {
            key: str(value).strip()
            for key, value in verified_structured_data.items()
            if str(value).strip()
        }
        return sanitized or None


class ProcessDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_processing_result_repository: DocumentProcessingResultRepository,
        document_processor: DocumentProcessor,
    ) -> None:
        self._document_repository = document_repository
        self._document_processing_result_repository = document_processing_result_repository
        self._document_processor = document_processor

    async def execute(self, document_id: UUID) -> DocumentReadModel:
        document = await self._document_repository.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document '{document_id}' was not found.")

        processing_document = await self._transition_status(
            document=document,
            new_status=DocumentProcessingStatus.PROCESSING,
        )

        try:
            processing_output = await self._document_processor.process(processing_document)
        except Exception as exc:
            failed_document = await self._finalize_processing(
                document=processing_document,
                new_status=DocumentProcessingStatus.FAILED,
                result_status=DocumentProcessingResultStatus.FAILED,
                processing_output=DocumentProcessingOutput(),
                error_message=str(exc),
            )
            return DocumentReadModel.model_validate(failed_document, from_attributes=True)

        processed_document = await self._finalize_processing(
            document=processing_document,
            new_status=DocumentProcessingStatus.PROCESSED,
            result_status=DocumentProcessingResultStatus.PROCESSED,
            processing_output=processing_output,
            error_message=None,
        )
        return DocumentReadModel.model_validate(processed_document, from_attributes=True)

    async def _transition_status(
        self,
        *,
        document: Document,
        new_status: DocumentProcessingStatus,
    ) -> Document:
        if not is_valid_document_processing_status_transition(
            document.processing_status,
            new_status,
        ):
            raise InvalidDocumentProcessingStatusTransitionError(
                "Cannot transition document processing status from "
                f"'{document.processing_status.value}' to '{new_status.value}'."
            )

        updated_document = await self._document_repository.update_processing_status(
            document_id=document.id,
            new_status=new_status,
            updated_at=datetime.now(UTC),
        )
        await self._document_repository.save_changes()
        return updated_document

    async def _finalize_processing(
        self,
        *,
        document: Document,
        new_status: DocumentProcessingStatus,
        result_status: DocumentProcessingResultStatus,
        processing_output: DocumentProcessingOutput,
        error_message: str | None,
    ) -> Document:
        if not is_valid_document_processing_status_transition(
            document.processing_status,
            new_status,
        ):
            raise InvalidDocumentProcessingStatusTransitionError(
                "Cannot transition document processing status from "
                f"'{document.processing_status.value}' to '{new_status.value}'."
            )

        now = datetime.now(UTC)
        updated_document = await self._document_repository.update_processing_status(
            document_id=document.id,
            new_status=new_status,
            updated_at=now,
        )
        await self._document_processing_result_repository.upsert(
            DocumentProcessingResult(
                id=uuid4(),
                document_id=updated_document.id,
                organization_id=updated_document.organization_id,
                status=result_status,
                extracted_text=processing_output.extracted_text,
                summary=processing_output.summary,
                detected_document_type=processing_output.detected_document_type,
                structured_data=processing_output.structured_data,
                error_message=error_message,
                processed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        await self._document_repository.save_changes()
        return updated_document
