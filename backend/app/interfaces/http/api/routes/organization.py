from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.authorization import (
    MembershipAuthorizationService,
    MembershipPermission,
)
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.application.organization_memberships.commands import (
    UpdateOrganizationMembershipRoleCommand,
    UpdateOrganizationMembershipStatusCommand,
)
from app.application.organization_memberships.schemas import (
    OrganizationMembershipOptionReadModel,
    OrganizationMembershipReadModel,
)
from app.application.organization_memberships.services import (
    ListOrganizationMembershipsUseCase,
    UpdateOrganizationMembershipRoleUseCase,
    UpdateOrganizationMembershipStatusUseCase,
)
from app.infrastructure.database.session import get_db_session
from app.infrastructure.organization_memberships.repositories import (
    SqlAlchemyOrganizationMembershipRepository,
)
from app.infrastructure.users.repositories import SqlAlchemyUserRepository
from app.interfaces.http.dependencies import (
    get_current_membership,
    require_membership_permission,
)
from app.interfaces.http.schemas.organization_memberships import (
    UpdateOrganizationMembershipRoleRequest,
    UpdateOrganizationMembershipStatusRequest,
)

router = APIRouter(prefix="/organization", tags=["organization"])


@router.get(
    "/members",
    response_model=list[OrganizationMembershipOptionReadModel],
)
async def list_organization_members(
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_MEMBERS)
    ),
) -> list[OrganizationMembershipOptionReadModel]:
    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    user_repository = SqlAlchemyUserRepository(session=session)
    use_case = ListOrganizationMembershipsUseCase(
        organization_membership_repository=membership_repository,
        user_repository=user_repository,
    )
    return await use_case.execute(current_membership.organization_id)


@router.patch(
    "/members/{membership_id}/role",
    response_model=OrganizationMembershipReadModel,
)
async def update_organization_member_role(
    membership_id: UUID,
    payload: UpdateOrganizationMembershipRoleRequest,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.MANAGE_MEMBERS)
    ),
) -> OrganizationMembershipReadModel:
    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    use_case = UpdateOrganizationMembershipRoleUseCase(
        organization_membership_repository=membership_repository,
        authorization_service=MembershipAuthorizationService(),
    )
    return await use_case.execute(
        membership_id,
        UpdateOrganizationMembershipRoleCommand(
            organization_id=current_membership.organization_id,
            actor_membership_id=current_membership.id,
            role=payload.role,
        ),
    )


@router.patch(
    "/members/{membership_id}/status",
    response_model=OrganizationMembershipReadModel,
)
async def update_organization_member_status(
    membership_id: UUID,
    payload: UpdateOrganizationMembershipStatusRequest,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.MANAGE_MEMBERS)
    ),
) -> OrganizationMembershipReadModel:
    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    use_case = UpdateOrganizationMembershipStatusUseCase(
        organization_membership_repository=membership_repository,
        authorization_service=MembershipAuthorizationService(),
    )
    return await use_case.execute(
        membership_id,
        UpdateOrganizationMembershipStatusCommand(
            organization_id=current_membership.organization_id,
            actor_membership_id=current_membership.id,
            status=payload.status,
        ),
    )
