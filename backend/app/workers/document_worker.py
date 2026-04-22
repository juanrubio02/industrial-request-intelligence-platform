import asyncio

from app.core.settings import get_settings
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.storage.local import LocalDocumentStorage
from app.interfaces.http.services import build_document_processing_worker


async def run_document_worker(*, poll_interval_seconds: float = 1.0) -> None:
    settings = get_settings()
    worker = build_document_processing_worker(
        session_factory=get_session_factory(settings),
        document_storage=LocalDocumentStorage(base_path=settings.documents_storage_dir),
    )

    while True:
        processed = await worker.run_once()
        if not processed:
            await asyncio.sleep(poll_interval_seconds)


def main() -> None:
    asyncio.run(run_document_worker())


if __name__ == "__main__":
    main()
