from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.commands import LoginCommand
from app.application.auth.password import PasswordHasher
from app.application.auth.schemas import (
    AccessTokenReadModel,
    AuthenticatedMembershipOptionReadModel,
    AuthenticatedUserReadModel,
)
from app.application.auth.services import (
    GetAuthenticatedUserUseCase,
    ListAuthenticatedMembershipsUseCase,
    LoginUserUseCase,
)
from app.application.auth.tokens import AccessTokenService
from app.infrastructure.database.session import get_db_session
from app.infrastructure.organization_memberships.repositories import (
    SqlAlchemyOrganizationMembershipRepository,
)
from app.infrastructure.organizations.repositories import SqlAlchemyOrganizationRepository
from app.infrastructure.users.repositories import SqlAlchemyUserRepository
from app.interfaces.http.dependencies import (
    get_access_token_service,
    get_current_user,
    get_password_hasher,
)
from app.interfaces.http.schemas.auth import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AccessTokenReadModel, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    access_token_service: AccessTokenService = Depends(get_access_token_service),
) -> AccessTokenReadModel:
    user_repository = SqlAlchemyUserRepository(session=session)
    use_case = LoginUserUseCase(
        user_repository=user_repository,
        password_hasher=password_hasher,
        access_token_service=access_token_service,
    )
    command = LoginCommand(email=payload.email, password=payload.password)
    return await use_case.execute(command)


@router.get("/me", response_model=AuthenticatedUserReadModel)
async def get_me(
    current_user: AuthenticatedUserReadModel = Depends(get_current_user),
) -> AuthenticatedUserReadModel:
    return current_user


@router.get("/memberships", response_model=list[AuthenticatedMembershipOptionReadModel])
async def list_my_memberships(
    current_user: AuthenticatedUserReadModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[AuthenticatedMembershipOptionReadModel]:
    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    organization_repository = SqlAlchemyOrganizationRepository(session=session)
    use_case = ListAuthenticatedMembershipsUseCase(
        organization_membership_repository=membership_repository,
        organization_repository=organization_repository,
    )
    return await use_case.execute(current_user_id=current_user.id)
