from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.application.common.pagination import PaginatedResult, PaginationParams
from app.application.auth.commands import LoginCommand
from app.application.auth.exceptions import (
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidMembershipContextError,
    InvalidRefreshTokenError,
)
from app.application.auth.password import PasswordHasher
from app.application.auth.schemas import (
    ActiveMembershipSummaryReadModel,
    AuthenticatedOrganizationReadModel,
    AuthenticatedSessionReadModel,
    AuthenticatedSessionUserReadModel,
    AuthenticatedMembershipReadModel,
    AuthenticatedMembershipOptionReadModel,
    AuthenticatedUserReadModel,
)
from app.application.auth.tokens import TokenService
from app.domain.auth_sessions.entities import AuthSession
from app.domain.auth_sessions.repositories import AuthSessionRepository
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.users.repositories import UserRepository


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _build_auth_session(user_id: UUID, *, ttl_seconds: int) -> AuthSession:
    issued_at = _utcnow()
    return AuthSession(
        id=uuid4(),
        user_id=user_id,
        expires_at=issued_at + timedelta(seconds=ttl_seconds),
        revoked_at=None,
        replaced_by_session_id=None,
        created_at=issued_at,
        updated_at=issued_at,
    )


class LoginUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        auth_session_repository: AuthSessionRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        *,
        access_token_ttl_seconds: int,
        refresh_token_ttl_seconds: int,
        authenticated_session_user_use_case: "BuildAuthenticatedSessionUserUseCase | None" = None,
    ) -> None:
        self._user_repository = user_repository
        self._auth_session_repository = auth_session_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._access_token_ttl_seconds = access_token_ttl_seconds
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self._authenticated_session_user_use_case = authenticated_session_user_use_case

    async def execute(self, command: LoginCommand) -> AuthenticatedSessionReadModel:
        user = await self._user_repository.get_by_email(command.email)
        if user is None or not self._password_hasher.verify(command.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise InvalidCredentialsError("User account is inactive.")

        refresh_session = _build_auth_session(
            user.id,
            ttl_seconds=self._refresh_token_ttl_seconds,
        )
        await self._auth_session_repository.add(refresh_session)
        access_token = self._token_service.issue_access_token(user.id)
        refresh_token = self._token_service.issue_refresh_token(user.id, refresh_session.id)
        authenticated_user = AuthenticatedUserReadModel.model_validate(user, from_attributes=True)
        if self._authenticated_session_user_use_case is None:
            session_user = AuthenticatedSessionUserReadModel(
                **authenticated_user.model_dump()
            )
        else:
            session_user = await self._authenticated_session_user_use_case.execute(
                current_user=authenticated_user,
                membership_id=None,
            )

        return AuthenticatedSessionReadModel(
            user=session_user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_token_ttl_seconds,
            refresh_expires_in=self._refresh_token_ttl_seconds,
        )


class GetAuthenticatedUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service

    async def execute(self, token: str) -> AuthenticatedUserReadModel:
        user_id = self._token_service.verify_access_token(token)
        user = await self._user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidAccessTokenError("Invalid or expired access token.")

        return AuthenticatedUserReadModel.model_validate(user, from_attributes=True)


class RefreshSessionUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        auth_session_repository: AuthSessionRepository,
        token_service: TokenService,
        *,
        access_token_ttl_seconds: int,
        refresh_token_ttl_seconds: int,
        authenticated_session_user_use_case: "BuildAuthenticatedSessionUserUseCase | None" = None,
    ) -> None:
        self._user_repository = user_repository
        self._auth_session_repository = auth_session_repository
        self._token_service = token_service
        self._access_token_ttl_seconds = access_token_ttl_seconds
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self._authenticated_session_user_use_case = authenticated_session_user_use_case

    async def execute(self, refresh_token: str) -> AuthenticatedSessionReadModel:
        refresh_claims = self._token_service.verify_refresh_token(refresh_token)
        current_session = await self._auth_session_repository.get_by_id(
            refresh_claims.token_id
        )
        now = _utcnow()
        if (
            current_session is None
            or current_session.user_id != refresh_claims.user_id
            or current_session.expires_at <= now
        ):
            raise InvalidRefreshTokenError("Invalid or expired refresh token.")

        if current_session.revoked_at is not None:
            await self._auth_session_repository.revoke_all_by_user_id(
                refresh_claims.user_id,
                revoked_at=now,
            )
            raise InvalidRefreshTokenError("Invalid or expired refresh token.")

        user = await self._user_repository.get_by_id(refresh_claims.user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError("Invalid or expired refresh token.")

        replacement_session = _build_auth_session(
            user.id,
            ttl_seconds=self._refresh_token_ttl_seconds,
        )
        try:
            await self._auth_session_repository.rotate(
                current_session_id=current_session.id,
                replacement_session=replacement_session,
                revoked_at=now,
            )
        except ValueError as exc:
            raise InvalidRefreshTokenError("Invalid or expired refresh token.") from exc

        authenticated_user = AuthenticatedUserReadModel.model_validate(user, from_attributes=True)
        if self._authenticated_session_user_use_case is None:
            session_user = AuthenticatedSessionUserReadModel(
                **authenticated_user.model_dump()
            )
        else:
            session_user = await self._authenticated_session_user_use_case.execute(
                current_user=authenticated_user,
                membership_id=None,
            )

        return AuthenticatedSessionReadModel(
            user=session_user,
            access_token=self._token_service.issue_access_token(user.id),
            refresh_token=self._token_service.issue_refresh_token(
                user.id,
                replacement_session.id,
            ),
            expires_in=self._access_token_ttl_seconds,
            refresh_expires_in=self._refresh_token_ttl_seconds,
        )


class LogoutSessionUseCase:
    def __init__(
        self,
        auth_session_repository: AuthSessionRepository,
        token_service: TokenService,
    ) -> None:
        self._auth_session_repository = auth_session_repository
        self._token_service = token_service

    async def execute(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return

        try:
            refresh_claims = self._token_service.verify_refresh_token(refresh_token)
        except InvalidRefreshTokenError:
            return

        auth_session = await self._auth_session_repository.get_by_id(refresh_claims.token_id)
        if auth_session is None or auth_session.user_id != refresh_claims.user_id:
            return

        if auth_session.revoked_at is not None:
            return

        await self._auth_session_repository.revoke(
            auth_session.id,
            revoked_at=_utcnow(),
        )


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
        membership_id: UUID | None,
    ) -> AuthenticatedMembershipReadModel:
        if membership_id is None:
            memberships = await self._organization_membership_repository.list_active_by_user_id(
                current_user_id
            )
            membership = memberships[0] if memberships else None
        else:
            membership = await self._organization_membership_repository.get_by_id(
                membership_id
            )

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
        pagination: PaginationParams,
    ) -> PaginatedResult[AuthenticatedMembershipOptionReadModel]:
        memberships = await self._organization_membership_repository.list_active_by_user_id(
            current_user_id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        total = await self._organization_membership_repository.count_active_by_user_id(
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
                    organization_slug=organization.slug,
                    role=membership.role,
                    status=membership.status,
                    joined_at=membership.joined_at,
                    created_at=membership.created_at,
                    updated_at=membership.updated_at,
                )
            )

        return PaginatedResult(
            items=membership_options,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )


class BuildAuthenticatedSessionUserUseCase:
    def __init__(
        self,
        authenticated_membership_use_case: GetAuthenticatedMembershipUseCase,
        organization_repository: OrganizationRepository,
    ) -> None:
        self._authenticated_membership_use_case = authenticated_membership_use_case
        self._organization_repository = organization_repository

    async def execute(
        self,
        *,
        current_user: AuthenticatedUserReadModel,
        membership_id: UUID | None,
    ) -> AuthenticatedSessionUserReadModel:
        try:
            active_membership = await self._authenticated_membership_use_case.execute(
                current_user_id=current_user.id,
                membership_id=membership_id,
            )
        except InvalidMembershipContextError:
            active_membership = None

        if active_membership is None:
            return AuthenticatedSessionUserReadModel(
                **current_user.model_dump(),
                active_organization=None,
                active_membership=None,
            )

        organization = await self._organization_repository.get_by_id(
            active_membership.organization_id
        )
        if organization is None:
            raise InvalidMembershipContextError("Membership context is invalid.")

        return AuthenticatedSessionUserReadModel(
            **current_user.model_dump(),
            active_organization=AuthenticatedOrganizationReadModel(
                id=organization.id,
                name=organization.name,
                slug=organization.slug,
            ),
            active_membership=ActiveMembershipSummaryReadModel(
                id=active_membership.id,
                role=active_membership.role,
                status=active_membership.status,
            ),
        )
