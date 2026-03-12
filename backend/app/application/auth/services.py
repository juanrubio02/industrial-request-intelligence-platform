from uuid import UUID

from app.application.auth.commands import LoginCommand
from app.application.auth.exceptions import (
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidMembershipContextError,
)
from app.application.auth.password import PasswordHasher
from app.application.auth.schemas import (
    AccessTokenReadModel,
    AuthenticatedMembershipReadModel,
    AuthenticatedMembershipOptionReadModel,
    AuthenticatedUserReadModel,
)
from app.application.auth.tokens import AccessTokenService
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.users.repositories import UserRepository


class LoginUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        access_token_service: AccessTokenService,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._access_token_service = access_token_service

    async def execute(self, command: LoginCommand) -> AccessTokenReadModel:
        user = await self._user_repository.get_by_email(command.email)
        if user is None or not self._password_hasher.verify(command.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise InvalidCredentialsError("User account is inactive.")

        return AccessTokenReadModel(access_token=self._access_token_service.issue(user.id))


class GetAuthenticatedUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        access_token_service: AccessTokenService,
    ) -> None:
        self._user_repository = user_repository
        self._access_token_service = access_token_service

    async def execute(self, token: str) -> AuthenticatedUserReadModel:
        user_id = self._access_token_service.verify(token)
        user = await self._user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidAccessTokenError("Invalid or expired access token.")

        return AuthenticatedUserReadModel.model_validate(user, from_attributes=True)


class GetAuthenticatedMembershipUseCase:
    def __init__(
        self,
        organization_membership_repository: OrganizationMembershipRepository,
    ) -> None:
        self._organization_membership_repository = organization_membership_repository

    async def execute(
        self,
        *,
        current_user_id: UUID,
        membership_id: UUID,
    ) -> AuthenticatedMembershipReadModel:
        membership = await self._organization_membership_repository.get_by_id(membership_id)
        if membership is None or membership.user_id != current_user_id or not membership.is_active:
            raise InvalidMembershipContextError("Membership context is invalid.")

        return AuthenticatedMembershipReadModel.model_validate(
            membership,
            from_attributes=True,
        )


class ListAuthenticatedMembershipsUseCase:
    def __init__(
        self,
        organization_membership_repository: OrganizationMembershipRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self._organization_membership_repository = organization_membership_repository
        self._organization_repository = organization_repository

    async def execute(
        self,
        *,
        current_user_id: UUID,
    ) -> list[AuthenticatedMembershipOptionReadModel]:
        memberships = await self._organization_membership_repository.list_active_by_user_id(
            current_user_id
        )

        membership_options: list[AuthenticatedMembershipOptionReadModel] = []
        for membership in memberships:
            organization = await self._organization_repository.get_by_id(
                membership.organization_id
            )
            if organization is None:
                continue

            membership_options.append(
                AuthenticatedMembershipOptionReadModel(
                    id=membership.id,
                    organization_id=membership.organization_id,
                    organization_name=organization.name,
                    role=membership.role,
                    is_active=membership.is_active,
                    created_at=membership.created_at,
                    updated_at=membership.updated_at,
                )
            )

        return membership_options
