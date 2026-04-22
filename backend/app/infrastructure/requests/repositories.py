from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.requests.entities import Request
from app.domain.requests.repositories import RequestRepository
from app.domain.requests.sources import RequestSource
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
            customer_id=request.customer_id,
            assigned_membership_id=request.assigned_membership_id,
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

    async def get_by_id_and_organization(
        self,
        request_id: UUID,
        organization_id: UUID,
    ) -> Request | None:
        statement = select(RequestModel).where(
            RequestModel.id == request_id,
            RequestModel.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_organization_id(self, organization_id: UUID) -> list[Request]:
        return await self.list_by_organization_filters(organization_id)

    async def list_by_organization_filters(
        self,
        organization_id: UUID,
        *,
        q: str | None = None,
        status: RequestStatus | None = None,
        customer_id: UUID | None = None,
        assigned_membership_id: UUID | None = None,
        source: RequestSource | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Request]:
        statement = (
            select(RequestModel)
            .where(RequestModel.organization_id == organization_id)
            .order_by(RequestModel.created_at.desc(), RequestModel.id.desc())
        )
        if q:
            statement = statement.where(RequestModel.title.ilike(f"%{q}%"))
        if status is not None:
            statement = statement.where(RequestModel.status == status)
        if customer_id is not None:
            statement = statement.where(RequestModel.customer_id == customer_id)
        if assigned_membership_id is not None:
            statement = statement.where(
                RequestModel.assigned_membership_id == assigned_membership_id
            )
        if source is not None:
            statement = statement.where(RequestModel.source == source)
        if offset:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def count_by_organization_filters(
        self,
        organization_id: UUID,
        *,
        q: str | None = None,
        status: RequestStatus | None = None,
        customer_id: UUID | None = None,
        assigned_membership_id: UUID | None = None,
        source: RequestSource | None = None,
    ) -> int:
        statement = select(func.count(RequestModel.id)).where(
            RequestModel.organization_id == organization_id
        )
        if q:
            statement = statement.where(RequestModel.title.ilike(f"%{q}%"))
        if status is not None:
            statement = statement.where(RequestModel.status == status)
        if customer_id is not None:
            statement = statement.where(RequestModel.customer_id == customer_id)
        if assigned_membership_id is not None:
            statement = statement.where(
                RequestModel.assigned_membership_id == assigned_membership_id
            )
        if source is not None:
            statement = statement.where(RequestModel.source == source)
        result = await self._session.execute(statement)
        return int(result.scalar() or 0)

    async def update(self, request: Request) -> Request:
        model = await self._session.get(RequestModel, request.id)
        if model is None:
            raise ValueError(f"Request '{request.id}' was not found.")

        model.title = request.title
        model.description = request.description
        model.customer_id = request.customer_id
        model.updated_at = request.updated_at
        return self._to_domain(model)

    async def update_status(
        self,
        request_id: UUID,
        organization_id: UUID,
        new_status: RequestStatus,
        updated_at: datetime,
    ) -> Request:
        statement = select(RequestModel).where(
            RequestModel.id == request_id,
            RequestModel.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Request '{request_id}' was not found.")

        model.status = new_status
        model.updated_at = updated_at
        return self._to_domain(model)

    async def update_assignment(
        self,
        request_id: UUID,
        assigned_membership_id: UUID | None,
        updated_at: datetime,
    ) -> Request:
        model = await self._session.get(RequestModel, request_id)
        if model is None:
            raise ValueError(f"Request '{request_id}' was not found.")

        model.assigned_membership_id = assigned_membership_id
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
            assigned_membership_id=model.assigned_membership_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            customer_id=model.customer_id,
        )
