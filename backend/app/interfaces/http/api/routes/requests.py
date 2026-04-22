from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.application.auth.authorization import MembershipPermission
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.application.request_activities.schemas import RequestActivityReadModel
from app.application.request_comments.commands import CreateRequestCommentCommand
from app.application.request_comments.schemas import RequestCommentReadModel
from app.application.requests.commands import (
    AssignRequestCommand,
    CreateRequestCommand,
    ListRequestsFilters,
    TransitionRequestStatusCommand,
    UpdateRequestCommand,
)
from app.application.requests.schemas import RequestReadModel
from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus
from app.interfaces.http.dependencies import (
    get_service_factory,
    require_membership_permission,
)
from app.interfaces.http.pagination import Pagination
from app.interfaces.http.responses import paginated_response, success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse, PaginatedResponse
from app.interfaces.http.schemas.request_comments import CreateRequestCommentRequest
from app.interfaces.http.schemas.requests import (
    AssignRequestRequest,
    CreateRequestRequest,
    TransitionRequestStatusRequest,
    UpdateRequestRequest,
)
from app.interfaces.http.services import ServiceFactory

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post(
    "",
    response_model=ApiSuccessResponse[RequestReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def create_request(
    payload: CreateRequestRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_REQUEST)
    ),
) -> ApiSuccessResponse[RequestReadModel]:
    return success_response(
        await services.create_request_use_case.execute(
            current_membership.organization_id,
            CreateRequestCommand(
                title=payload.title,
                description=payload.description,
                source=payload.source,
                created_by_membership_id=current_membership.id,
                customer_id=payload.customer_id,
            ),
        )
    )


@router.get(
    "",
    response_model=PaginatedResponse[RequestReadModel],
)
async def list_requests(
    pagination: Pagination,
    q: str | None = Query(default=None, max_length=255),
    status: RequestStatus | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    assigned_membership_id: UUID | None = Query(default=None),
    source: RequestSource | None = Query(default=None),
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_REQUESTS)
    ),
) -> PaginatedResponse[RequestReadModel]:
    result = await services.list_requests_use_case.execute(
        current_membership.organization_id,
        ListRequestsFilters(
            q=q,
            status=status,
            customer_id=customer_id,
            assigned_membership_id=assigned_membership_id,
            source=source,
        ),
        pagination,
    )
    return paginated_response(result)


@router.get(
    "/{request_id}",
    response_model=ApiSuccessResponse[RequestReadModel],
)
async def get_request(
    request_id: UUID,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_REQUESTS)
    ),
) -> ApiSuccessResponse[RequestReadModel]:
    return success_response(
        await services.get_request_by_id_use_case.execute(
            request_id,
            current_membership.organization_id,
        )
    )


@router.patch(
    "/{request_id}",
    response_model=ApiSuccessResponse[RequestReadModel],
)
async def update_request(
    request_id: UUID,
    payload: UpdateRequestRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_REQUEST)
    ),
) -> ApiSuccessResponse[RequestReadModel]:
    return success_response(
        await services.update_request_use_case.execute(
            request_id=request_id,
            organization_id=current_membership.organization_id,
            command=UpdateRequestCommand(
                **payload.model_dump(exclude_unset=True),
                membership_id=current_membership.id,
                user_id=current_membership.user_id,
            ),
        )
    )


@router.get(
    "/{request_id}/activities",
    response_model=PaginatedResponse[RequestActivityReadModel],
)
async def list_request_activities(
    request_id: UUID,
    pagination: Pagination,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_REQUESTS)
    ),
) -> PaginatedResponse[RequestActivityReadModel]:
    result = await services.list_request_activities_use_case.execute(
        request_id,
        current_membership.organization_id,
        pagination,
    )
    return paginated_response(result)


@router.get(
    "/{request_id}/comments",
    response_model=PaginatedResponse[RequestCommentReadModel],
)
async def list_request_comments(
    request_id: UUID,
    pagination: Pagination,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_REQUESTS)
    ),
) -> PaginatedResponse[RequestCommentReadModel]:
    result = await services.list_request_comments_use_case.execute(
        request_id,
        current_membership.organization_id,
        pagination,
    )
    return paginated_response(result)


@router.post(
    "/{request_id}/comments",
    response_model=ApiSuccessResponse[RequestCommentReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def create_request_comment(
    request_id: UUID,
    payload: CreateRequestCommentRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.COMMENT_ON_REQUEST)
    ),
) -> ApiSuccessResponse[RequestCommentReadModel]:
    return success_response(
        await services.create_request_comment_use_case.execute(
            request_id,
            CreateRequestCommentCommand(
                organization_id=current_membership.organization_id,
                membership_id=current_membership.id,
                body=payload.body,
            ),
        )
    )


@router.post(
    "/{request_id}/status-transitions",
    response_model=ApiSuccessResponse[RequestReadModel],
)
async def transition_request_status(
    request_id: UUID,
    payload: TransitionRequestStatusRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.TRANSITION_REQUEST_STATUS)
    ),
) -> ApiSuccessResponse[RequestReadModel]:
    return success_response(
        await services.transition_request_status_use_case.execute(
            request_id=request_id,
            command=TransitionRequestStatusCommand(
                organization_id=current_membership.organization_id,
                membership_id=current_membership.id,
                user_id=current_membership.user_id,
                new_status=payload.new_status,
            ),
        )
    )


@router.patch(
    "/{request_id}/assign",
    response_model=ApiSuccessResponse[RequestReadModel],
)
async def assign_request(
    request_id: UUID,
    payload: AssignRequestRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.ASSIGN_REQUEST)
    ),
) -> ApiSuccessResponse[RequestReadModel]:
    return success_response(
        await services.assign_request_use_case.execute(
            request_id=request_id,
            command=AssignRequestCommand(
                organization_id=current_membership.organization_id,
                membership_id=current_membership.id,
                assigned_membership_id=payload.assigned_membership_id,
            ),
        )
    )
