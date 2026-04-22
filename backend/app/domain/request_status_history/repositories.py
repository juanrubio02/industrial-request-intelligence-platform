from abc import ABC, abstractmethod

from app.domain.request_status_history.entities import RequestStatusHistoryEntry


class RequestStatusHistoryRepository(ABC):
    @abstractmethod
    async def add(
        self,
        entry: RequestStatusHistoryEntry,
    ) -> RequestStatusHistoryEntry:
        raise NotImplementedError
