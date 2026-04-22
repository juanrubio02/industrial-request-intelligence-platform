from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.auth.authorization import MembershipPermission
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.application.common.exceptions import AuthorizationError
from app.application.organization_memberships.commands import (
    CreateOrganizationMembershipCommand,
    UpdateOrganizationMembershipRoleCommand,
    UpdateOrganizationMembershipStatusCommand,
)
from app.application.organization_memberships.schemas import (
    OrganizationMembershipOptionReadModel,
    OrganizationMembershipReadModel,
)
from app.interfaces.http.dependencies import (
    get_service_factory,
    require_membership_permission,
)
from app.interfaces.http.pagination import Pagination
from app.interfaces.http.responses import paginated_response, success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse, PaginatedResponse
from app.interfaces.http.schemas.organization_memberships import (
    CreateOrganizationMembershipRequest,
    UpdateOrganizationMembershipRoleRequest,
    UpdateOrganizationMembershipStatusRequest,
)
from app.interfaces.http.services import ServiceFactory

router = APIRouter(prefix="/organizations/{organization_id}/memberships", tags=["memberships"])


def _assert_same_organization(
    organization_id: UUID,
    current_membership: AuthenticatedMembershipReadModel,
) -> None:
    if current_membership.organization_id != organization_id:
        raise AuthorizationError("You do not have access to this organization.")


@router.post(
    "",
    response_model=ApiSuccessResponse[OrganizationMembershipReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def create_organization_membership(
    organization_id: UUID,
    payload: CreateOrganizationMembershipRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.MANAGE_MEMBERS)
    ),
) -> ApiSuccessResponse[OrganizationMembershipReadModel]:
    _assert_same_organization(organization_id, current_membership)
    return success_response(
        await services.create_organization_membership_use_case.execute(
            CreateOrganizationMembershipCommand(
                organization_id=organization_id,
                user_id=payload.user_id,
                role=payload.role,
            )
        )
    )


@router.get(
    "",
    response_model=PaginatedResponse[OrganizationMembershipOptionReadModel],
)
async def list_organization_memberships(
    organization_id: UUID,
    pagination: Pagination,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_MEMBERS)
    ),
) -> PaginatedResponse[OrganizationMembershipOptionReadModel]:
    _assert_same_organization(organization_id, current_membership)
    result = await services.list_organization_memberships_use_case.execute(
        organization_id=organization_id,
        pagination=pagination,
    )
    return paginated_response(result)


@router.get(
    "/{membership_id}",
    response_model=ApiSuccessResponse[OrganizationMembershipReadModel],
)
async def get_organization_membership(
    organization_id: UUID,
    membership_id: UUID,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_MEMBERS)
    ),
) -> ApiSuccessResponse[OrganizationMembershipReadModel]:
    _assert_same_organization(organization_id, current_membership)
    return success_response(
        await services.get_organization_membership_use_case.execute(
            organization_id=organization_id,
            membership_id=membership_id,
        )
    )


@router.patch(
    "/{membership_id}/role",
    response_model=ApiSuccessResponse[OrganizationMembershipReadModel],
)
async def update_organization_member_role(
    organization_id: UUID,
    membership_id: UUID,
    payload: UpdateOrganizationMembershipRoleRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.MANAGE_MEMBERS)
    ),
) -> ApiSuccessResponse[OrganizationMembershipReadModel]:
    _assert_same_organization(organization_id, current_membership)
    return success_response(
        await services.update_organization_membership_role_use_case.execute(
            membership_id,
            UpdateOrganizationMembershipRoleCommand(
                organization_id=organization_id,
                actor_membership_id=current_membership.id,
                role=payload.role,
            ),
        )
    )


@router.patch(
    "/{membership_id}/status",
    response_model=ApiSuccessResponse[OrganizationMembershipReadModel],
)
async def update_organization_member_status(
    organization_id: UUID,
    membership_id: UUID,
    payload: UpdateOrganizationMembershipStatusRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.MANAGE_MEMBERS)
    ),
) -> ApiSuccessResponse[OrganizationMembershipReadModel]:
    _assert_same_organization(organization_id, current_membership)
    return success_response(
        await services.update_organization_membership_status_use_case.execute(
            membership_id,
            UpdateOrganizationMembershipStatusCommand(
                organization_id=organization_id,
                actor_membership_id=current_membership.id,
                status=payload.status,
            ),
        )
    )
