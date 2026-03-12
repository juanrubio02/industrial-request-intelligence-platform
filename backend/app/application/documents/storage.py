from abc import ABC, abstractmethod


class DocumentStorage(ABC):
    @abstractmethod
    async def save(
        self,
        *,
        storage_key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, *, storage_key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def read(self, *, storage_key: str) -> bytes:
        raise NotImplementedError
