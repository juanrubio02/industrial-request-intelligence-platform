from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.documents.processing import DocumentProcessor
from app.application.documents.services import ProcessDocumentUseCase
from app.infrastructure.document_processing_results.repositories import (
    SqlAlchemyDocumentProcessingResultRepository,
)
from app.infrastructure.documents.repositories import SqlAlchemyDocumentRepository


class DocumentProcessingWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        document_processor: DocumentProcessor,
    ) -> None:
        self._session_factory = session_factory
        self._document_processor = document_processor

    async def process(self, document_id: UUID) -> None:
        async with self._session_factory() as session:
            document_repository = SqlAlchemyDocumentRepository(session=session)
            document_processing_result_repository = SqlAlchemyDocumentProcessingResultRepository(
                session=session
            )
            use_case = ProcessDocumentUseCase(
                document_repository=document_repository,
                document_processing_result_repository=document_processing_result_repository,
                document_processor=self._document_processor,
            )
            await use_case.execute(document_id)
