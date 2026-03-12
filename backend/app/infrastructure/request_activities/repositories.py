from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.infrastructure.database.models.request_activity import RequestActivityModel


class SqlAlchemyRequestActivityRepository(RequestActivityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, activity: RequestActivity) -> RequestActivity:
        model = RequestActivityModel(
            id=activity.id,
            request_id=activity.request_id,
            organization_id=activity.organization_id,
            membership_id=activity.membership_id,
            type=activity.type,
            payload=activity.payload,
            created_at=activity.created_at,
        )
        self._session.add(model)
        return activity

    async def list_by_request_id(self, request_id: UUID) -> list[RequestActivity]:
        statement = (
            select(RequestActivityModel)
            .where(RequestActivityModel.request_id == request_id)
            .order_by(RequestActivityModel.created_at.asc(), RequestActivityModel.id.asc())
        )
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(model: RequestActivityModel) -> RequestActivity:
        return RequestActivity(
            id=model.id,
            request_id=model.request_id,
            organization_id=model.organization_id,
            membership_id=model.membership_id,
            type=model.type,
            payload=model.payload,
            created_at=model.created_at,
        )

