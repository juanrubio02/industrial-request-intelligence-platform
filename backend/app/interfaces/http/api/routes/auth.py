from fastapi import APIRouter, Depends, Request, Response, status

from app.application.auth.commands import LoginCommand
from app.application.auth.exceptions import InvalidRefreshTokenError
from app.application.auth.schemas import (
    AuthenticatedMembershipOptionReadModel,
    AuthenticatedSessionUserReadModel,
    LoginResponseReadModel,
)
from app.interfaces.http.auth_cookies import (
    clear_auth_session_cookie,
    set_auth_session_cookie,
)
from app.interfaces.http.dependencies import (
    get_current_session_user,
    get_service_factory,
    get_settings_dependency,
)
from app.interfaces.http.pagination import Pagination
from app.interfaces.http.responses import paginated_response, success_response
from app.interfaces.http.schemas.auth import LoginRequest
from app.interfaces.http.schemas.common import (
    ApiSuccessResponse,
    MessageResponse,
    PaginatedResponse,
)
from app.interfaces.http.services import ServiceFactory

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=ApiSuccessResponse[LoginResponseReadModel],
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    response: Response,
    settings=Depends(get_settings_dependency),
    services: ServiceFactory = Depends(get_service_factory),
) -> ApiSuccessResponse[LoginResponseReadModel]:
    authenticated_session = await services.login_user_use_case.execute(
        LoginCommand(email=payload.email, password=payload.password)
    )
    set_auth_session_cookie(
        response,
        settings=settings,
        access_token=authenticated_session.access_token,
        refresh_token=authenticated_session.refresh_token,
    )
    return success_response(
        LoginResponseReadModel(
            user=authenticated_session.user,
            access_token=authenticated_session.access_token,
            token_type=authenticated_session.token_type,
            expires_in=authenticated_session.expires_in,
        )
    )


@router.post(
    "/refresh",
    response_model=ApiSuccessResponse[LoginResponseReadModel],
    status_code=status.HTTP_200_OK,
)
async def refresh_session(
    request: Request,
    response: Response,
    settings=Depends(get_settings_dependency),
    services: ServiceFactory = Depends(get_service_factory),
) -> ApiSuccessResponse[LoginResponseReadModel]:
    refresh_token = request.cookies.get(settings.auth_refresh_cookie_name)
    if not refresh_token:
        raise InvalidRefreshTokenError("Invalid or expired refresh token.")

    authenticated_session = await services.refresh_session_use_case.execute(refresh_token)
    set_auth_session_cookie(
        response,
        settings=settings,
        access_token=authenticated_session.access_token,
        refresh_token=authenticated_session.refresh_token,
    )
    return success_response(
        LoginResponseReadModel(
            user=authenticated_session.user,
            access_token=authenticated_session.access_token,
            token_type=authenticated_session.token_type,
            expires_in=authenticated_session.expires_in,
        )
    )


@router.get(
    "/me",
    response_model=ApiSuccessResponse[AuthenticatedSessionUserReadModel],
)
async def get_me(
    current_user: AuthenticatedSessionUserReadModel = Depends(get_current_session_user),
) -> ApiSuccessResponse[AuthenticatedSessionUserReadModel]:
    return success_response(current_user)


@router.get(
    "/memberships",
    response_model=PaginatedResponse[AuthenticatedMembershipOptionReadModel],
)
async def list_my_memberships(
    pagination: Pagination,
    current_user: AuthenticatedSessionUserReadModel = Depends(get_current_session_user),
    services: ServiceFactory = Depends(get_service_factory),
) -> PaginatedResponse[AuthenticatedMembershipOptionReadModel]:
    result = await services.list_authenticated_memberships_use_case.execute(
        current_user_id=current_user.id,
        pagination=pagination,
    )
    return paginated_response(result)


@router.post(
    "/logout",
    response_model=ApiSuccessResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    response: Response,
    settings=Depends(get_settings_dependency),
    services: ServiceFactory = Depends(get_service_factory),
) -> ApiSuccessResponse[MessageResponse]:
    await services.logout_session_use_case.execute(
        request.cookies.get(settings.auth_refresh_cookie_name)
    )
    clear_auth_session_cookie(response, settings=settings)
    return success_response(MessageResponse(message="Logged out successfully."))
