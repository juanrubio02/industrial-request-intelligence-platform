from fastapi import APIRouter, Depends, status

from app.application.auth.authorization import MembershipPermission
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.application.users.commands import CreateUserCommand
from app.application.users.schemas import UserReadModel
from app.interfaces.http.dependencies import (
    get_service_factory,
    require_membership_permission,
)
from app.interfaces.http.responses import success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse
from app.interfaces.http.schemas.users import CreateUserRequest
from app.interfaces.http.services import ServiceFactory

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=ApiSuccessResponse[UserReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: CreateUserRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_USER)
    ),
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
