import pytest

from app.application.documents.exceptions import DocumentStoragePathError
from app.infrastructure.storage.local import LocalDocumentStorage


@pytest.mark.anyio
async def test_local_document_storage_saves_and_reads_valid_path(tmp_path) -> None:
    storage = LocalDocumentStorage(base_path=tmp_path / "documents")

    await storage.save(
        storage_key="documents/report.pdf",
        content=b"safe-content",
        content_type="application/pdf",
    )

    assert await storage.read(storage_key="documents/report.pdf") == b"safe-content"


@pytest.mark.anyio
async def test_local_document_storage_rejects_parent_traversal(tmp_path) -> None:
    storage = LocalDocumentStorage(base_path=tmp_path / "documents")

    with pytest.raises(DocumentStoragePathError):
        await storage.save(
            storage_key="../../etc/passwd",
            content=b"blocked",
            content_type="text/plain",
        )


@pytest.mark.anyio
async def test_local_document_storage_rejects_absolute_path(tmp_path) -> None:
    storage = LocalDocumentStorage(base_path=tmp_path / "documents")

    with pytest.raises(DocumentStoragePathError):
        await storage.read(storage_key="/etc/passwd")


@pytest.mark.anyio
async def test_local_document_storage_rejects_symlink_escape(tmp_path) -> None:
    storage = LocalDocumentStorage(base_path=tmp_path / "documents")
    storage.base_path.mkdir(parents=True, exist_ok=True)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (storage.base_path / "shared").symlink_to(outside_dir, target_is_directory=True)

    with pytest.raises(DocumentStoragePathError):
        await storage.save(
            storage_key="shared/escape.txt",
            content=b"blocked",
            content_type="text/plain",
        )
