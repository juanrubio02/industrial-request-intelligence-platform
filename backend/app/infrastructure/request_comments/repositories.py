from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.request_comments.entities import RequestComment
from app.domain.request_comments.repositories import RequestCommentRepository
from app.infrastructure.database.models.request_comment import RequestCommentModel


class SqlAlchemyRequestCommentRepository(RequestCommentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, comment: RequestComment) -> RequestComment:
        model = RequestCommentModel(
            id=comment.id,
            request_id=comment.request_id,
            organization_id=comment.organization_id,
            membership_id=comment.membership_id,
            body=comment.body,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
        self._session.add(model)
        return comment

    async def list_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[RequestComment]:
        statement = (
            select(RequestCommentModel)
            .where(
                RequestCommentModel.request_id == request_id,
                RequestCommentModel.organization_id == organization_id,
            )
            .order_by(RequestCommentModel.created_at.asc(), RequestCommentModel.id.asc())
        )
        if offset:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def count_by_request_id(
        self,
        request_id: UUID,
        *,
        organization_id: UUID,
    ) -> int:
        statement = select(func.count(RequestCommentModel.id)).where(
            RequestCommentModel.request_id == request_id,
            RequestCommentModel.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return int(result.scalar() or 0)

    async def count_by_request_ids(
        self,
        request_ids: Sequence[UUID],
        *,
        organization_id: UUID,
    ) -> dict[UUID, int]:
        if not request_ids:
            return {}

        statement = (
            select(RequestCommentModel.request_id, func.count(RequestCommentModel.id))
            .where(
                RequestCommentModel.organization_id == organization_id,
                RequestCommentModel.request_id.in_(request_ids),
            )
            .group_by(RequestCommentModel.request_id)
        )
        result = await self._session.execute(statement)
        return {request_id: count for request_id, count in result.all()}

    async def save_changes(self) -> None:
        await self._session.commit()

    @staticmethod
    def _to_domain(model: RequestCommentModel) -> RequestComment:
        return RequestComment(
            id=model.id,
            request_id=model.request_id,
            organization_id=model.organization_id,
            membership_id=model.membership_id,
            body=model.body,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
