from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.document_processing_results.entities import DocumentProcessingResult


class DocumentProcessingResultRepository(ABC):
    @abstractmethod
    async def save_changes(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def upsert(
        self,
        result: DocumentProcessingResult,
    ) -> DocumentProcessingResult:
        raise NotImplementedError

    @abstractmethod
    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentProcessingResult | None:
        raise NotImplementedError
