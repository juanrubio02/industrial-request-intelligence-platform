from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.requests.entities import Request
from app.domain.requests.statuses import RequestStatus


class RequestRepository(ABC):
    @abstractmethod
    async def add(self, request: Request) -> Request:
        raise NotImplementedError

    @abstractmethod
    async def save_changes(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, request_id: UUID) -> Request | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_organization_id(self, organization_id: UUID) -> list[Request]:
        raise NotImplementedError

    @abstractmethod
    async def update_status(
        self,
        request_id: UUID,
        new_status: RequestStatus,
        updated_at: datetime,
    ) -> Request:
        raise NotImplementedError
