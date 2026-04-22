from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.request_status_history.entities import RequestStatusHistoryEntry
from app.domain.request_status_history.repositories import RequestStatusHistoryRepository
from app.infrastructure.database.models.request_status_history import (
    RequestStatusHistoryModel,
)


class SqlAlchemyRequestStatusHistoryRepository(RequestStatusHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        entry: RequestStatusHistoryEntry,
    ) -> RequestStatusHistoryEntry:
        model = RequestStatusHistoryModel(
            id=entry.id,
            request_id=entry.request_id,
            organization_id=entry.organization_id,
            previous_status=entry.previous_status,
            new_status=entry.new_status,
            changed_at=entry.changed_at,
            changed_by=entry.changed_by,
            changed_by_user_id=entry.changed_by_user_id,
        )
        self._session.add(model)
        return entry
