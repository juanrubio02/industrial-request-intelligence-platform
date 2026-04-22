from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.request_activities.entities import RequestActivity


class RequestActivityRepository(ABC):
    @abstractmethod
    async def add(self, activity: RequestActivity) -> RequestActivity:
        raise NotImplementedError

    @abstractmethod
    async def list_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[RequestActivity]:
        raise NotImplementedError

    @abstractmethod
    async def count_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
    ) -> int:
        raise NotImplementedError
