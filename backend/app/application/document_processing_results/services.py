from uuid import UUID

from app.application.document_processing_results.exceptions import (
    DocumentProcessingResultNotFoundError,
)
from app.application.document_processing_results.schemas import (
    DocumentProcessingResultReadModel,
)
from app.application.documents.exceptions import DocumentNotFoundError
from app.domain.document_processing_results.repositories import (
    DocumentProcessingResultRepository,
)
from app.domain.documents.repositories import DocumentRepository


class GetDocumentProcessingResultByDocumentIdUseCase:
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_processing_result_repository: DocumentProcessingResultRepository,
    ) -> None:
        self._document_repository = document_repository
        self._document_processing_result_repository = document_processing_result_repository

    async def execute(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> DocumentProcessingResultReadModel:
        document = await self._document_repository.get_by_id(document_id)
        if document is None or document.organization_id != organization_id:
            raise DocumentNotFoundError(f"Document '{document_id}' was not found.")

        result = await self._document_processing_result_repository.get_by_document_id(document_id)
        if result is None:
            raise DocumentProcessingResultNotFoundError(
                f"Document processing result for document '{document_id}' was not found."
            )

        return DocumentProcessingResultReadModel.model_validate(result, from_attributes=True)
