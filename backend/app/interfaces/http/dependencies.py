from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.authorization import (
    MembershipAuthorizationService,
    MembershipPermission,
)
from app.application.auth.exceptions import (
    InvalidAccessTokenError,
    InvalidMembershipContextError,
)
from app.application.auth.password import PasswordHasher
from app.application.auth.schemas import (
    AuthenticatedMembershipReadModel,
    AuthenticatedOrganizationReadModel,
    AuthenticatedSessionUserReadModel,
    AuthenticatedUserReadModel,
)
from app.application.auth.tokens import TokenService
from app.application.documents.processing import DocumentProcessingDispatcher
from app.application.documents.storage import DocumentStorage
from app.application.health.service import HealthService
from app.core.settings import Settings, get_settings
from app.infrastructure.auth.password import ScryptPasswordHasher
from app.infrastructure.auth.tokens import JwtTokenService
from app.infrastructure.database.session import get_db_session
from app.infrastructure.document_processing_jobs.repositories import (
    SqlAlchemyDocumentProcessingJobRepository,
)
from app.infrastructure.document_processing.dispatcher import (
    DatabaseDocumentProcessingDispatcher,
)
from app.infrastructure.storage.local import LocalDocumentStorage
from app.interfaces.http.logging import bind_log_context
from app.interfaces.http.schemas.common import ApiErrorResponse
from app.interfaces.http.services import ServiceFactory, build_health_service


def get_settings_dependency() -> Settings:
    return get_settings()


def get_health_service(
    settings: Settings = Depends(get_settings_dependency),
) -> HealthService:
    return build_health_service(settings)


def get_password_hasher() -> PasswordHasher:
    return ScryptPasswordHasher()


def get_token_service(
    settings: Settings = Depends(get_settings_dependency),
) -> TokenService:
    return JwtTokenService(
        secret_key=settings.auth_secret_key,
        access_token_ttl_seconds=settings.auth_access_token_ttl_seconds,
        refresh_token_ttl_seconds=settings.auth_refresh_token_ttl_seconds,
    )


def get_membership_authorization_service() -> MembershipAuthorizationService:
    return MembershipAuthorizationService()


def _extract_access_token(request: Request, settings: Settings) -> str | None:
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token.strip()

    cookie_token = request.cookies.get(settings.auth_session_cookie_name)
    if cookie_token:
        return cookie_token

    return None


def get_document_storage(
    settings: Settings = Depends(get_settings_dependency),
) -> DocumentStorage:
    return LocalDocumentStorage(base_path=settings.documents_storage_dir)


def get_document_processing_dispatcher(
    session: AsyncSession = Depends(get_db_session),
) -> DocumentProcessingDispatcher:
    return DatabaseDocumentProcessingDispatcher(
        job_repository=SqlAlchemyDocumentProcessingJobRepository(session=session)
    )


def get_service_factory(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
    document_storage: DocumentStorage = Depends(get_document_storage),
    document_processing_dispatcher: DocumentProcessingDispatcher = Depends(
        get_document_processing_dispatcher
    ),
) -> ServiceFactory:
    return ServiceFactory(
        session=session,
        settings=settings,
        password_hasher=password_hasher,
        token_service=token_service,
        document_storage=document_storage,
        document_processing_dispatcher=document_processing_dispatcher,
    )


def require_bootstrap_key(
    request: Request,
    bootstrap_key: str | None = Header(default=None, alias="X-Bootstrap-Key"),
    settings: Settings = Depends(get_settings_dependency),
) -> None:
    if bootstrap_key != settings.bootstrap_api_key:
        error = ApiErrorResponse(
            error={
                "type": "BootstrapAuthorizationError",
                "message": "A valid bootstrap key is required.",
                "request_id": getattr(request.state, "request_id", None),
            }
        )
        raise InvalidAccessTokenError(error.error.message)


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings_dependency),
    services: ServiceFactory = Depends(get_service_factory),
) -> AuthenticatedUserReadModel:
    token = _extract_access_token(request, settings)
    if token is None:
        raise InvalidAccessTokenError("Invalid or expired access token.")

    authenticated_user = await services.get_authenticated_user_use_case.execute(token)
    request.state.access_token = token
    request.state.authenticated_user_id = authenticated_user.id
    bind_log_context(user_id=str(authenticated_user.id))
    return authenticated_user


async def get_current_session_user(
    request: Request,
    current_user: AuthenticatedUserReadModel = Depends(get_current_user),
    active_membership_id: UUID | None = Header(default=None, alias="X-Membership-Id"),
    services: ServiceFactory = Depends(get_service_factory),
) -> AuthenticatedSessionUserReadModel:
    session_user = await services.build_authenticated_session_user_use_case.execute(
        current_user=current_user,
        membership_id=active_membership_id,
    )
    if session_user.active_membership is not None:
        request.state.active_membership_id = session_user.active_membership.id
        bind_log_context(membership_id=str(session_user.active_membership.id))
    if session_user.active_organization is not None:
        request.state.organization_id = session_user.active_organization.id
        bind_log_context(organization_id=str(session_user.active_organization.id))
    return session_user


async def get_current_membership(
    request: Request,
    current_user: AuthenticatedUserReadModel = Depends(get_current_user),
    active_membership_id: UUID | None = Header(default=None, alias="X-Membership-Id"),
    services: ServiceFactory = Depends(get_service_factory),
) -> AuthenticatedMembershipReadModel:
    request.state.active_membership_id = active_membership_id
    if active_membership_id is not None:
        bind_log_context(membership_id=str(active_membership_id))
    if active_membership_id is None:
        raise InvalidMembershipContextError("A valid membership context is required.")

    membership = await services.get_authenticated_membership_use_case.execute(
        current_user_id=current_user.id,
        membership_id=active_membership_id,
    )
    request.state.active_membership_id = membership.id
    request.state.organization_id = membership.organization_id
    bind_log_context(
        membership_id=str(membership.id),
        organization_id=str(membership.organization_id),
    )
    return membership


async def get_current_organization(
    current_membership: AuthenticatedMembershipReadModel = Depends(get_current_membership),
    services: ServiceFactory = Depends(get_service_factory),
) -> AuthenticatedOrganizationReadModel:
    organization = await services.organization_repository.get_by_id(
        current_membership.organization_id
    )
    if organization is None or not organization.is_active:
        raise InvalidMembershipContextError("Membership context is invalid.")

    return AuthenticatedOrganizationReadModel(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
    )


def require_membership_permission(permission: MembershipPermission):
    async def dependency(
        current_membership: AuthenticatedMembershipReadModel = Depends(
            get_current_membership
        ),
        authorization_service: MembershipAuthorizationService = Depends(
            get_membership_authorization_service
        ),
    ) -> AuthenticatedMembershipReadModel:
        authorization_service.authorize(
            membership=current_membership,
            permission=permission,
        )
        return current_membership

    return dependency
