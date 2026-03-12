from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
    AuthenticatedUserReadModel,
)
from app.application.auth.services import (
    GetAuthenticatedMembershipUseCase,
    GetAuthenticatedUserUseCase,
)
from app.application.auth.tokens import AccessTokenService
from app.application.documents.processing import DocumentProcessingDispatcher
from app.application.documents.processing import DocumentProcessor
from app.application.documents.storage import DocumentStorage
from app.application.health.service import HealthService
from app.core.settings import get_settings
from app.infrastructure.auth.password import ScryptPasswordHasher
from app.infrastructure.auth.tokens import HmacAccessTokenService
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.database.session import get_db_session
from app.infrastructure.document_processing.dispatcher import (
    AsyncioDocumentProcessingDispatcher,
)
from app.infrastructure.document_processing.processor import StorageBackedDocumentProcessor
from app.infrastructure.document_processing.worker import DocumentProcessingWorker
from app.infrastructure.storage.local import LocalDocumentStorage
from app.infrastructure.organization_memberships.repositories import (
    SqlAlchemyOrganizationMembershipRepository,
)
from app.infrastructure.users.repositories import SqlAlchemyUserRepository

http_bearer = HTTPBearer(auto_error=False)


def get_health_service() -> HealthService:
    return HealthService(settings=get_settings())


def get_password_hasher() -> PasswordHasher:
    return ScryptPasswordHasher()


def get_access_token_service() -> AccessTokenService:
    settings = get_settings()
    return HmacAccessTokenService(
        secret_key=settings.auth_secret_key,
        ttl_seconds=settings.auth_token_ttl_seconds,
    )


def get_membership_authorization_service() -> MembershipAuthorizationService:
    return MembershipAuthorizationService()


def get_document_storage() -> DocumentStorage:
    settings = get_settings()
    return LocalDocumentStorage(base_path=settings.documents_storage_dir)


def get_document_processor() -> DocumentProcessor:
    return StorageBackedDocumentProcessor(document_storage=get_document_storage())


def get_document_processing_worker() -> DocumentProcessingWorker:
    return DocumentProcessingWorker(
        session_factory=get_session_factory(),
        document_processor=get_document_processor(),
    )


def get_document_processing_dispatcher() -> DocumentProcessingDispatcher:
    return AsyncioDocumentProcessingDispatcher(worker=get_document_processing_worker())


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    session: AsyncSession = Depends(get_db_session),
    access_token_service: AccessTokenService = Depends(get_access_token_service),
) -> AuthenticatedUserReadModel:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidAccessTokenError("Invalid or expired access token.")

    user_repository = SqlAlchemyUserRepository(session=session)
    use_case = GetAuthenticatedUserUseCase(
        user_repository=user_repository,
        access_token_service=access_token_service,
    )
    return await use_case.execute(credentials.credentials)


async def get_current_membership(
    current_user: AuthenticatedUserReadModel = Depends(get_current_user),
    membership_id: UUID | None = Header(default=None, alias="X-Membership-Id"),
    session: AsyncSession = Depends(get_db_session),
) -> AuthenticatedMembershipReadModel:
    if membership_id is None:
        raise InvalidMembershipContextError("A valid membership context is required.")

    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    use_case = GetAuthenticatedMembershipUseCase(
        organization_membership_repository=membership_repository,
    )
    return await use_case.execute(
        current_user_id=current_user.id,
        membership_id=membership_id,
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
