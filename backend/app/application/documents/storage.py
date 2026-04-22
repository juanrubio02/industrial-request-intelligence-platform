import string
from abc import ABC, abstractmethod
from pathlib import PurePath
from uuid import uuid4

_ALLOWED_EXTENSION_CHARACTERS = frozenset(string.ascii_lowercase + string.digits)
_MAX_EXTENSION_LENGTH = 16


def generate_storage_key(filename: str) -> str:
    suffix = _sanitize_extension(filename)
    return f"documents/{uuid4().hex}{suffix}"


def _sanitize_extension(filename: str) -> str:
    suffix = PurePath(filename).suffix.lower()
    if not suffix.startswith("."):
        return ""

    extension = suffix[1:]
    if not extension or len(extension) > _MAX_EXTENSION_LENGTH:
        return ""

    if any(character not in _ALLOWED_EXTENSION_CHARACTERS for character in extension):
        return ""

    return f".{extension}"


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
