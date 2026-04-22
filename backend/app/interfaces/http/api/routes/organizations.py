from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.auth.authorization import MembershipPermission
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.application.common.exceptions import AuthorizationError
from app.application.organizations.commands import CreateOrganizationCommand
from app.application.organizations.schemas import OrganizationReadModel
from app.interfaces.http.dependencies import (
    get_service_factory,
    require_membership_permission,
)
from app.interfaces.http.responses import success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse
from app.interfaces.http.schemas.organizations import CreateOrganizationRequest
from app.interfaces.http.services import ServiceFactory

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post(
    "",
    response_model=ApiSuccessResponse[OrganizationReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    payload: CreateOrganizationRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_ORGANIZATION)
    ),
) -> ApiSuccessResponse[OrganizationReadModel]:
    organization = await services.create_organization_use_case.execute(
        CreateOrganizationCommand(name=payload.name, slug=payload.slug)
    )
    return success_response(organization)


@router.get(
    "/{organization_id}",
    response_model=ApiSuccessResponse[OrganizationReadModel],
)
async def get_organization(
    organization_id: UUID,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_MEMBERS)
    ),
) -> ApiSuccessResponse[OrganizationReadModel]:
    if current_membership.organization_id != organization_id:
        raise AuthorizationError("You do not have access to this organization.")

    return success_response(
        await services.get_organization_by_id_use_case.execute(organization_id)
    )
