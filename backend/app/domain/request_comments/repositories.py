from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.domain.request_comments.entities import RequestComment


class RequestCommentRepository(ABC):
    @abstractmethod
    async def add(self, comment: RequestComment) -> RequestComment:
        raise NotImplementedError

    @abstractmethod
    async def list_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[RequestComment]:
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
    async def save_changes(self) -> None:
        raise NotImplementedError
