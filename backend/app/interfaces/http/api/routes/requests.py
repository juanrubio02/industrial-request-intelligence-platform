from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.authorization import MembershipPermission
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.application.request_activities.schemas import RequestActivityReadModel
from app.application.requests.commands import CreateRequestCommand
from app.application.requests.commands import TransitionRequestStatusCommand
from app.application.requests.schemas import RequestReadModel
from app.application.requests.services import (
    CreateRequestUseCase,
    GetRequestByIdUseCase,
    ListRequestsUseCase,
    ListRequestActivitiesUseCase,
    TransitionRequestStatusUseCase,
)
from app.infrastructure.database.session import get_db_session
from app.infrastructure.organization_memberships.repositories import (
    SqlAlchemyOrganizationMembershipRepository,
)
from app.infrastructure.organizations.repositories import SqlAlchemyOrganizationRepository
from app.infrastructure.request_activities.repositories import (
    SqlAlchemyRequestActivityRepository,
)
from app.infrastructure.requests.repositories import SqlAlchemyRequestRepository
from app.interfaces.http.dependencies import get_current_membership
from app.interfaces.http.dependencies import require_membership_permission
from app.interfaces.http.schemas.requests import CreateRequestRequest
from app.interfaces.http.schemas.requests import TransitionRequestStatusRequest

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=RequestReadModel, status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: CreateRequestRequest,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_REQUEST)
    ),
) -> RequestReadModel:
    request_repository = SqlAlchemyRequestRepository(session=session)
    request_activity_repository = SqlAlchemyRequestActivityRepository(session=session)
    organization_repository = SqlAlchemyOrganizationRepository(session=session)
    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    use_case = CreateRequestUseCase(
        request_repository=request_repository,
        request_activity_repository=request_activity_repository,
        organization_repository=organization_repository,
        organization_membership_repository=membership_repository,
    )
    command = CreateRequestCommand(
        organization_id=current_membership.organization_id,
        title=payload.title,
        description=payload.description,
        source=payload.source,
        created_by_membership_id=current_membership.id,
    )
    return await use_case.execute(command)


@router.get("", response_model=list[RequestReadModel])
async def list_requests(
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        get_current_membership
    ),
) -> list[RequestReadModel]:
    repository = SqlAlchemyRequestRepository(session=session)
    use_case = ListRequestsUseCase(request_repository=repository)
    return await use_case.execute(current_membership.organization_id)


@router.get("/{request_id}", response_model=RequestReadModel)
async def get_request(
    request_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        get_current_membership
    ),
) -> RequestReadModel:
    repository = SqlAlchemyRequestRepository(session=session)
    use_case = GetRequestByIdUseCase(request_repository=repository)
    return await use_case.execute(request_id, current_membership.organization_id)


@router.get("/{request_id}/activities", response_model=list[RequestActivityReadModel])
async def list_request_activities(
    request_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        get_current_membership
    ),
) -> list[RequestActivityReadModel]:
    request_repository = SqlAlchemyRequestRepository(session=session)
    activity_repository = SqlAlchemyRequestActivityRepository(session=session)
    use_case = ListRequestActivitiesUseCase(
        request_repository=request_repository,
        request_activity_repository=activity_repository,
    )
    return await use_case.execute(request_id, current_membership.organization_id)


@router.post("/{request_id}/status-transitions", response_model=RequestReadModel)
async def transition_request_status(
    request_id: UUID,
    payload: TransitionRequestStatusRequest,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.TRANSITION_REQUEST_STATUS)
    ),
) -> RequestReadModel:
    request_repository = SqlAlchemyRequestRepository(session=session)
    activity_repository = SqlAlchemyRequestActivityRepository(session=session)
    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
        request_activity_repository=activity_repository,
        organization_membership_repository=membership_repository,
    )
    command = TransitionRequestStatusCommand(
        organization_id=current_membership.organization_id,
        membership_id=current_membership.id,
        new_status=payload.new_status,
    )
    return await use_case.execute(request_id=request_id, command=command)
