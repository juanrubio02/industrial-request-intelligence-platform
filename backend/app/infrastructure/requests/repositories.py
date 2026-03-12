from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.requests.entities import Request
from app.domain.requests.repositories import RequestRepository
from app.domain.requests.statuses import RequestStatus
from app.infrastructure.database.models.request import RequestModel


class SqlAlchemyRequestRepository(RequestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, request: Request) -> Request:
        model = RequestModel(
            id=request.id,
            organization_id=request.organization_id,
            title=request.title,
            description=request.description,
            status=request.status,
            source=request.source,
            created_by_membership_id=request.created_by_membership_id,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )
        self._session.add(model)
        return request

    async def save_changes(self) -> None:
        await self._session.commit()

    async def get_by_id(self, request_id: UUID) -> Request | None:
        model = await self._session.get(RequestModel, request_id)
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_organization_id(self, organization_id: UUID) -> list[Request]:
        statement = (
            select(RequestModel)
            .where(RequestModel.organization_id == organization_id)
            .order_by(RequestModel.created_at.desc(), RequestModel.id.desc())
        )
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update_status(
        self,
        request_id: UUID,
        new_status: RequestStatus,
        updated_at: datetime,
    ) -> Request:
        model = await self._session.get(RequestModel, request_id)
        if model is None:
            raise ValueError(f"Request '{request_id}' was not found.")

        model.status = new_status
        model.updated_at = updated_at
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: RequestModel) -> Request:
        return Request(
            id=model.id,
            organization_id=model.organization_id,
            title=model.title,
            description=model.description,
            status=model.status,
            source=model.source,
            created_by_membership_id=model.created_by_membership_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
