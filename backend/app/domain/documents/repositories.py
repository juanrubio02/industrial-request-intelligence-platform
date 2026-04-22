from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.documents.entities import Document
from app.domain.documents.statuses import DocumentProcessingStatus


class DocumentRepository(ABC):
    @abstractmethod
    async def add(self, document: Document) -> Document:
        raise NotImplementedError

    @abstractmethod
    async def save_changes(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Document | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Document]:
        raise NotImplementedError

    @abstractmethod
    async def count_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_by_request_ids(
        self,
        request_ids: Sequence[UUID],
        *,
        organization_id: UUID,
    ) -> dict[UUID, int]:
        raise NotImplementedError

    @abstractmethod
    async def update_processing_status(
        self,
        document_id: UUID,
        new_status: DocumentProcessingStatus,
        updated_at: datetime,
    ) -> Document:
        raise NotImplementedError

    @abstractmethod
    async def update_verified_structured_data(
        self,
        document_id: UUID,
        verified_structured_data: dict[str, Any] | None,
        updated_at: datetime,
    ) -> Document:
        raise NotImplementedError
