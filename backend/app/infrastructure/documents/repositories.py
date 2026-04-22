from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.documents.exceptions import DocumentStorageKeyAlreadyExistsError
from app.domain.documents.entities import Document
from app.domain.documents.repositories import DocumentRepository
from app.domain.documents.statuses import DocumentProcessingStatus
from app.infrastructure.database.models.document import DocumentModel


class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, document: Document) -> Document:
        model = DocumentModel(
            id=document.id,
            request_id=document.request_id,
            organization_id=document.organization_id,
            uploaded_by_membership_id=document.uploaded_by_membership_id,
            original_filename=document.original_filename,
            storage_key=document.storage_key,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            processing_status=document.processing_status,
            verified_structured_data=document.verified_structured_data,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        self._session.add(model)
        return document

    async def save_changes(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if self._is_storage_key_violation(exc):
                raise DocumentStorageKeyAlreadyExistsError(
                    "Document storage key already exists."
                ) from exc
            raise

    async def get_by_id(self, document_id: UUID) -> Document | None:
        model = await self._session.get(DocumentModel, document_id)
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Document]:
        statement = (
            select(DocumentModel)
            .where(
                DocumentModel.request_id == request_id,
                DocumentModel.organization_id == organization_id,
            )
            .order_by(DocumentModel.created_at.asc(), DocumentModel.id.asc())
        )
        if offset:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def count_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
    ) -> int:
        statement = select(func.count(DocumentModel.id)).where(
            DocumentModel.request_id == request_id,
            DocumentModel.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return int(result.scalar() or 0)

    async def count_by_request_ids(
        self,
        request_ids: Sequence[UUID],
        *,
        organization_id: UUID,
    ) -> dict[UUID, int]:
        if not request_ids:
            return {}

        statement = (
            select(DocumentModel.request_id, func.count(DocumentModel.id))
            .where(
                DocumentModel.organization_id == organization_id,
                DocumentModel.request_id.in_(request_ids),
            )
            .group_by(DocumentModel.request_id)
        )
        result = await self._session.execute(statement)
        return {request_id: count for request_id, count in result.all()}

    async def update_processing_status(
        self,
        document_id: UUID,
        new_status: DocumentProcessingStatus,
        updated_at: datetime,
    ) -> Document:
        model = await self._session.get(DocumentModel, document_id)
        if model is None:
            raise ValueError(f"Document '{document_id}' was not found.")

        model.processing_status = new_status
        model.updated_at = updated_at
        return self._to_domain(model)

    async def update_verified_structured_data(
        self,
        document_id: UUID,
        verified_structured_data: dict[str, Any] | None,
        updated_at: datetime,
    ) -> Document:
        model = await self._session.get(DocumentModel, document_id)
        if model is None:
            raise ValueError(f"Document '{document_id}' was not found.")

        model.verified_structured_data = verified_structured_data
        model.updated_at = updated_at
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            request_id=model.request_id,
            organization_id=model.organization_id,
            uploaded_by_membership_id=model.uploaded_by_membership_id,
            original_filename=model.original_filename,
            storage_key=model.storage_key,
            content_type=model.content_type,
            size_bytes=model.size_bytes,
            processing_status=model.processing_status,
            verified_structured_data=model.verified_structured_data,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _is_storage_key_violation(exc: IntegrityError) -> bool:
        original_error = getattr(exc, "orig", None)
        return (
            getattr(original_error, "sqlstate", None) == "23505"
            and getattr(original_error, "constraint_name", None) == "uq_documents_storage_key"
        )
