from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.pagination import PaginatedResult, PaginationParams
from app.application.request_comments.commands import CreateRequestCommentCommand
from app.application.request_comments.schemas import RequestCommentReadModel
from app.application.requests.exceptions import RequestNotFoundError
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.domain.request_comments.entities import RequestComment
from app.domain.request_comments.repositories import RequestCommentRepository
from app.domain.requests.repositories import RequestRepository


class CreateRequestCommentUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_comment_repository: RequestCommentRepository,
        request_activity_repository: RequestActivityRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_comment_repository = request_comment_repository
        self._request_activity_repository = request_activity_repository

    async def execute(
        self,
        request_id: UUID,
        command: CreateRequestCommentCommand,
    ) -> RequestCommentReadModel:
        request = await self._request_repository.get_by_id(request_id)
        if request is None or request.organization_id != command.organization_id:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        now = datetime.now(UTC)
        comment = RequestComment(
            id=uuid4(),
            request_id=request.id,
            organization_id=request.organization_id,
            membership_id=command.membership_id,
            body=command.body,
            created_at=now,
            updated_at=now,
        )
        created_comment = await self._request_comment_repository.add(comment)
        await self._request_activity_repository.add(
            RequestActivity(
                id=uuid4(),
                request_id=request.id,
                organization_id=request.organization_id,
                membership_id=command.membership_id,
                type=RequestActivityType.REQUEST_COMMENT_ADDED,
                payload={
                    "comment_id": str(created_comment.id),
                    "membership_id": str(command.membership_id),
                },
                created_at=now,
            )
        )
        await self._request_comment_repository.save_changes()
        return RequestCommentReadModel.model_validate(created_comment, from_attributes=True)


class ListRequestCommentsUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_comment_repository: RequestCommentRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_comment_repository = request_comment_repository

    async def execute(
        self,
        request_id: UUID,
        organization_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResult[RequestCommentReadModel]:
        request = await self._request_repository.get_by_id(request_id)
        if request is None or request.organization_id != organization_id:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        comments = await self._request_comment_repository.list_by_request_id(
            request_id,
            organization_id=organization_id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        total = await self._request_comment_repository.count_by_request_id(
            request_id,
            organization_id=organization_id,
        )
        return PaginatedResult(
            items=[
                RequestCommentReadModel.model_validate(comment, from_attributes=True)
                for comment in comments
            ],
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )
