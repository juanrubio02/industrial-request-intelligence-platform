from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.organization_memberships.commands import CreateOrganizationMembershipCommand
from app.application.organization_memberships.schemas import OrganizationMembershipReadModel
from app.application.organizations.commands import CreateOrganizationCommand
from app.application.organizations.schemas import OrganizationReadModel
from app.application.users.commands import CreateUserCommand
from app.application.users.schemas import UserReadModel
from app.interfaces.http.dependencies import (
    get_service_factory,
    require_bootstrap_key,
)
from app.interfaces.http.responses import success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse
from app.interfaces.http.schemas.organization_memberships import (
    CreateOrganizationMembershipRequest,
)
from app.interfaces.http.schemas.organizations import CreateOrganizationRequest
from app.interfaces.http.schemas.users import CreateUserRequest
from app.interfaces.http.services import ServiceFactory

router = APIRouter(prefix="/bootstrap", tags=["bootstrap"])


@router.post(
    "/users",
    response_model=ApiSuccessResponse[UserReadModel],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_bootstrap_key)],
)
async def bootstrap_create_user(
    payload: CreateUserRequest,
    services: ServiceFactory = Depends(get_service_factory),
) -> ApiSuccessResponse[UserReadModel]:
    return success_response(
        await services.create_user_use_case.execute(
            CreateUserCommand(
                email=payload.email,
                full_name=payload.full_name,
                password=payload.password,
            )
        )
    )


@router.post(
    "/organizations",
    response_model=ApiSuccessResponse[OrganizationReadModel],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_bootstrap_key)],
)
async def bootstrap_create_organization(
    payload: CreateOrganizationRequest,
    services: ServiceFactory = Depends(get_service_factory),
) -> ApiSuccessResponse[OrganizationReadModel]:
    return success_response(
        await services.create_organization_use_case.execute(
            CreateOrganizationCommand(name=payload.name, slug=payload.slug)
        )
    )


@router.post(
    "/organizations/{organization_id}/memberships",
    response_model=ApiSuccessResponse[OrganizationMembershipReadModel],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_bootstrap_key)],
)
async def bootstrap_create_organization_membership(
    organization_id: UUID,
    payload: CreateOrganizationMembershipRequest,
    services: ServiceFactory = Depends(get_service_factory),
) -> ApiSuccessResponse[OrganizationMembershipReadModel]:
    return success_response(
        await services.create_organization_membership_use_case.execute(
            CreateOrganizationMembershipCommand(
                organization_id=organization_id,
                user_id=payload.user_id,
                role=payload.role,
            )
        )
    )
