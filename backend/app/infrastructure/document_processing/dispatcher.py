import asyncio
from uuid import UUID

from app.application.documents.processing import DocumentProcessingDispatcher
from app.infrastructure.document_processing.worker import DocumentProcessingWorker


class AsyncioDocumentProcessingDispatcher(DocumentProcessingDispatcher):
    def __init__(self, worker: DocumentProcessingWorker) -> None:
        self._worker = worker

    async def enqueue(self, document_id: UUID) -> None:
        asyncio.create_task(self._run(document_id))

    async def _run(self, document_id: UUID) -> None:
        try:
            await self._worker.process(document_id)
        except Exception:
            return None
