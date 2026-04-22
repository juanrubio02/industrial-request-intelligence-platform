from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domain.document_processing_results.document_types import DocumentDetectedType
from app.domain.documents.entities import Document


class DocumentProcessor(ABC):
    @abstractmethod
    async def process(self, document: Document) -> "DocumentProcessingOutput":
        raise NotImplementedError


class DocumentProcessingDispatcher(ABC):
    @abstractmethod
    async def enqueue(self, document_id: UUID, organization_id: UUID) -> None:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class DocumentProcessingOutput:
    extracted_text: str | None = None
    summary: str | None = None
    detected_document_type: DocumentDetectedType | None = None
    structured_data: dict[str, Any] | None = None
