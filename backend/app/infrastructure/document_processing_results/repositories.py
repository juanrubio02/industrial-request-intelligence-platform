from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.document_processing_results.document_types import (
    DocumentDetectedType,
)
from app.domain.document_processing_results.entities import DocumentProcessingResult
from app.domain.document_processing_results.repositories import (
    DocumentProcessingResultRepository,
)
from app.infrastructure.database.models.document_processing_result import (
    DocumentProcessingResultModel,
)


class SqlAlchemyDocumentProcessingResultRepository(DocumentProcessingResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_changes(self) -> None:
        await self._session.commit()

    async def upsert(
        self,
        result: DocumentProcessingResult,
    ) -> DocumentProcessingResult:
        statement = select(DocumentProcessingResultModel).where(
            DocumentProcessingResultModel.document_id == result.document_id
        )
        existing_model = (await self._session.execute(statement)).scalar_one_or_none()

        if existing_model is None:
            model = DocumentProcessingResultModel(
                id=result.id,
                document_id=result.document_id,
                organization_id=result.organization_id,
                status=result.status,
                extracted_text=result.extracted_text,
                summary=result.summary,
                detected_document_type=(
                    result.detected_document_type.value
                    if result.detected_document_type is not None
                    else None
                ),
                structured_data=result.structured_data,
                error_message=result.error_message,
                processed_at=result.processed_at,
                created_at=result.created_at,
                updated_at=result.updated_at,
            )
            self._session.add(model)
            return result

        existing_model.organization_id = result.organization_id
        existing_model.status = result.status
        existing_model.extracted_text = result.extracted_text
        existing_model.summary = result.summary
        existing_model.detected_document_type = (
            result.detected_document_type.value
            if result.detected_document_type is not None
            else None
        )
        existing_model.structured_data = result.structured_data
        existing_model.error_message = result.error_message
        existing_model.processed_at = result.processed_at
        existing_model.updated_at = result.updated_at
        return self._to_domain(existing_model)

    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentProcessingResult | None:
        statement = select(DocumentProcessingResultModel).where(
            DocumentProcessingResultModel.document_id == document_id
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: DocumentProcessingResultModel) -> DocumentProcessingResult:
        return DocumentProcessingResult(
            id=model.id,
            document_id=model.document_id,
            organization_id=model.organization_id,
            status=model.status,
            extracted_text=model.extracted_text,
            summary=model.summary,
            detected_document_type=(
                DocumentDetectedType(model.detected_document_type)
                if model.detected_document_type is not None
                else None
            ),
            structured_data=model.structured_data,
            error_message=model.error_message,
            processed_at=model.processed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
