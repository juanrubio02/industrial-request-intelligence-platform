import asyncio
from pathlib import Path

from app.application.documents.storage import DocumentStorage


class LocalDocumentStorage(DocumentStorage):
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    @property
    def base_path(self) -> Path:
        return self._base_path

    async def save(
        self,
        *,
        storage_key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        target_path = self._resolve(storage_key)
        await asyncio.to_thread(target_path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(target_path.write_bytes, content)

    async def delete(self, *, storage_key: str) -> None:
        target_path = self._resolve(storage_key)
        if await asyncio.to_thread(target_path.exists):
            await asyncio.to_thread(target_path.unlink)

    async def read(self, *, storage_key: str) -> bytes:
        target_path = self._resolve(storage_key)
        return await asyncio.to_thread(target_path.read_bytes)

    def _resolve(self, storage_key: str) -> Path:
        return self._base_path / storage_key
