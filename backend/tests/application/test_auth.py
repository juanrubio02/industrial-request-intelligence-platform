from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.auth.commands import LoginCommand
from app.application.auth.exceptions import (
    InvalidCredentialsError,
    InvalidMembershipContextError,
    InvalidRefreshTokenError,
)
from app.application.common.pagination import PaginationParams
from app.application.auth.services import (
    BuildAuthenticatedSessionUserUseCase,
    GetAuthenticatedMembershipUseCase,
    GetAuthenticatedUserUseCase,
    ListAuthenticatedMembershipsUseCase,
    LoginUserUseCase,
    LogoutSessionUseCase,
    RefreshSessionUseCase,
)
from app.application.auth.schemas import AuthenticatedUserReadModel
from app.domain.auth_sessions.entities import AuthSession
from app.domain.auth_sessions.repositories import AuthSessionRepository
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus
from app.domain.organizations.entities import Organization
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.users.entities import User
from app.domain.users.repositories import UserRepository
from app.infrastructure.auth.password import ScryptPasswordHasher
from app.infrastructure.auth.tokens import JwtTokenService


class InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[User] | None = None) -> None:
        self._users_by_id = {user.id: user for user in users or []}
        self._users_by_email = {user.email: user for user in users or []}

    async def add(self, user: User) -> User:
        self._users_by_id[user.id] = user
        self._users_by_email[user.email] = user
        return user

    async def get_by_id(self, user_id):
        return self._users_by_id.get(user_id)

    async def get_by_email(self, email: str):
        return self._users_by_email.get(email)

    async def list_by_ids(self, user_ids):
        return [user for user_id, user in self._users_by_id.items() if user_id in user_ids]


class InMemoryOrganizationMembershipRepository(OrganizationMembershipRepository):
    def __init__(self, memberships: list[OrganizationMembership] | None = None) -> None:
        self._memberships = {membership.id: membership for membership in memberships or []}

    async def add(self, membership: OrganizationMembership) -> OrganizationMembership:
        self._memberships[membership.id] = membership
        return membership

    async def get_by_id(self, membership_id):
        return self._memberships.get(membership_id)

    async def get_by_id_and_organization(self, membership_id, organization_id):
        membership = self._memberships.get(membership_id)
        if membership is None or membership.organization_id != organization_id:
            return None
        return membership

    async def get_active_by_user_and_organization(self, user_id, organization_id):
        for membership in self._memberships.values():
            if (
                membership.user_id == user_id
                and membership.organization_id == organization_id
                and membership.is_active
            ):
                return membership
        return None

    async def list_active_by_user_id(self, user_id, *, limit=None, offset=0):
        memberships = [
            membership
            for membership in self._memberships.values()
            if membership.user_id == user_id and membership.is_active
        ]
        if limit is None:
            return memberships[offset:]
        return memberships[offset : offset + limit]

    async def count_active_by_user_id(self, user_id):
        return len(
            [
                membership
                for membership in self._memberships.values()
                if membership.user_id == user_id and membership.is_active
            ]
        )

    async def list_active_by_organization_id(self, organization_id, *, limit=None, offset=0):
        memberships = [
            membership
            for membership in self._memberships.values()
            if membership.organization_id == organization_id and membership.is_active
        ]
        if limit is None:
            return memberships[offset:]
        return memberships[offset : offset + limit]

    async def list_by_organization_id(self, organization_id, *, limit=None, offset=0):
        memberships = [
            membership
            for membership in self._memberships.values()
            if membership.organization_id == organization_id
        ]
        if limit is None:
            return memberships[offset:]
        return memberships[offset : offset + limit]

    async def count_by_organization_id(self, organization_id):
        return len(
            [
                membership
                for membership in self._memberships.values()
                if membership.organization_id == organization_id
            ]
        )

    async def list_by_ids_and_organization(self, membership_ids, organization_id):
        return [
            membership
            for membership in self._memberships.values()
            if membership.id in membership_ids and membership.organization_id == organization_id
        ]

    async def save(self, membership: OrganizationMembership) -> OrganizationMembership:
        self._memberships[membership.id] = membership
        return membership

    async def count_active_by_organization_and_role(self, organization_id, role):
        return sum(
            1
            for membership in self._memberships.values()
            if membership.organization_id == organization_id
            and membership.role == role
            and membership.is_active
        )


class InMemoryOrganizationRepository(OrganizationRepository):
    def __init__(self, organizations: list[Organization] | None = None) -> None:
        self._organizations = {organization.id: organization for organization in organizations or []}

    async def add(self, organization: Organization) -> Organization:
        self._organizations[organization.id] = organization
        return organization

    async def get_by_id(self, organization_id):
        return self._organizations.get(organization_id)

    async def get_by_slug(self, slug: str):
        for organization in self._organizations.values():
            if organization.slug == slug:
                return organization
        return None


class InMemoryAuthSessionRepository(AuthSessionRepository):
    def __init__(self, auth_sessions: list[AuthSession] | None = None) -> None:
        self._auth_sessions = {
            auth_session.id: auth_session for auth_session in auth_sessions or []
        }

    async def add(self, auth_session: AuthSession) -> AuthSession:
        self._auth_sessions[auth_session.id] = auth_session
        return auth_session

    async def get_by_id(self, auth_session_id):
        return self._auth_sessions.get(auth_session_id)

    async def rotate(self, *, current_session_id, replacement_session, revoked_at):
        current_session = self._auth_sessions[current_session_id]
        self._auth_sessions[current_session_id] = AuthSession(
            id=current_session.id,
            user_id=current_session.user_id,
            expires_at=current_session.expires_at,
            revoked_at=revoked_at,
            replaced_by_session_id=replacement_session.id,
            created_at=current_session.created_at,
            updated_at=revoked_at,
        )
        self._auth_sessions[replacement_session.id] = replacement_session
        return replacement_session

    async def revoke(self, auth_session_id, *, revoked_at):
        auth_session = self._auth_sessions[auth_session_id]
        self._auth_sessions[auth_session_id] = AuthSession(
            id=auth_session.id,
            user_id=auth_session.user_id,
            expires_at=auth_session.expires_at,
            revoked_at=revoked_at,
            replaced_by_session_id=auth_session.replaced_by_session_id,
            created_at=auth_session.created_at,
            updated_at=revoked_at,
        )

    async def revoke_all_by_user_id(self, user_id, *, revoked_at):
        revoked_count = 0
        for auth_session in list(self._auth_sessions.values()):
            if auth_session.user_id != user_id or auth_session.revoked_at is not None:
                continue

            self._auth_sessions[auth_session.id] = AuthSession(
                id=auth_session.id,
                user_id=auth_session.user_id,
                expires_at=auth_session.expires_at,
                revoked_at=revoked_at,
                replaced_by_session_id=auth_session.replaced_by_session_id,
                created_at=auth_session.created_at,
                updated_at=revoked_at,
            )
            revoked_count += 1

        return revoked_count


def _user(password: str = "StrongPass123!") -> User:
    now = datetime.now(UTC)
    password_hasher = ScryptPasswordHasher()
    return User(
        id=uuid4(),
        email="alice@example.com",
        full_name="Alice Example",
        password_hash=password_hasher.hash(password),
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _membership(user_id, *, is_active: bool = True) -> OrganizationMembership:
    now = datetime.now(UTC)
    return OrganizationMembership(
        id=uuid4(),
        organization_id=uuid4(),
        user_id=user_id,
        role=OrganizationMembershipRole.ADMIN,
        status=(
            OrganizationMembershipStatus.ACTIVE
            if is_active
            else OrganizationMembershipStatus.DISABLED
        ),
        joined_at=now,
        created_at=now,
        updated_at=now,
    )


def _organization(name: str, slug: str) -> Organization:
    now = datetime.now(UTC)
    return Organization(
        id=uuid4(),
        name=name,
        slug=slug,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_login_user_use_case_returns_authenticated_session_for_valid_credentials() -> None:
    repository = InMemoryUserRepository(users=[_user()])
    auth_session_repository = InMemoryAuthSessionRepository()
    use_case = LoginUserUseCase(
        user_repository=repository,
        auth_session_repository=auth_session_repository,
        password_hasher=ScryptPasswordHasher(),
        token_service=JwtTokenService(
            secret_key="test-auth-secret",
            access_token_ttl_seconds=3600,
            refresh_token_ttl_seconds=86400,
        ),
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )

    result = await use_case.execute(
        LoginCommand(email="alice@example.com", password="StrongPass123!")
    )

    assert result.user.email == "alice@example.com"
    assert result.user.full_name == "Alice Example"
    assert result.token_type == "bearer"
    assert result.access_token
    assert result.refresh_token


@pytest.mark.anyio
async def test_login_user_use_case_rejects_invalid_credentials() -> None:
    repository = InMemoryUserRepository(users=[_user()])
    auth_session_repository = InMemoryAuthSessionRepository()
    use_case = LoginUserUseCase(
        user_repository=repository,
        auth_session_repository=auth_session_repository,
        password_hasher=ScryptPasswordHasher(),
        token_service=JwtTokenService(
            secret_key="test-auth-secret",
            access_token_ttl_seconds=3600,
            refresh_token_ttl_seconds=86400,
        ),
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginCommand(email="alice@example.com", password="WrongPass123!")
        )


@pytest.mark.anyio
async def test_refresh_session_use_case_rotates_refresh_token() -> None:
    user = _user()
    user_repository = InMemoryUserRepository(users=[user])
    auth_session_repository = InMemoryAuthSessionRepository()
    token_service = JwtTokenService(
        secret_key="test-auth-secret",
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )
    login_use_case = LoginUserUseCase(
        user_repository=user_repository,
        auth_session_repository=auth_session_repository,
        password_hasher=ScryptPasswordHasher(),
        token_service=token_service,
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )
    refresh_use_case = RefreshSessionUseCase(
        user_repository=user_repository,
        auth_session_repository=auth_session_repository,
        token_service=token_service,
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )

    login_result = await login_use_case.execute(
        LoginCommand(email="alice@example.com", password="StrongPass123!")
    )
    initial_claims = token_service.verify_refresh_token(login_result.refresh_token)

    refreshed_result = await refresh_use_case.execute(login_result.refresh_token)
    refreshed_claims = token_service.verify_refresh_token(refreshed_result.refresh_token)

    assert refreshed_result.refresh_token != login_result.refresh_token
    assert refreshed_claims.token_id != initial_claims.token_id
    revoked_session = await auth_session_repository.get_by_id(initial_claims.token_id)
    replacement_session = await auth_session_repository.get_by_id(refreshed_claims.token_id)
    assert revoked_session is not None
    assert revoked_session.revoked_at is not None
    assert revoked_session.replaced_by_session_id == refreshed_claims.token_id
    assert replacement_session is not None
    assert replacement_session.revoked_at is None


@pytest.mark.anyio
async def test_refresh_session_use_case_revokes_active_sessions_on_replay_attempt() -> None:
    user = _user()
    user_repository = InMemoryUserRepository(users=[user])
    auth_session_repository = InMemoryAuthSessionRepository()
    token_service = JwtTokenService(
        secret_key="test-auth-secret",
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )
    login_use_case = LoginUserUseCase(
        user_repository=user_repository,
        auth_session_repository=auth_session_repository,
        password_hasher=ScryptPasswordHasher(),
        token_service=token_service,
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )
    refresh_use_case = RefreshSessionUseCase(
        user_repository=user_repository,
        auth_session_repository=auth_session_repository,
        token_service=token_service,
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )

    login_result = await login_use_case.execute(
        LoginCommand(email="alice@example.com", password="StrongPass123!")
    )
    refreshed_result = await refresh_use_case.execute(login_result.refresh_token)
    refreshed_claims = token_service.verify_refresh_token(refreshed_result.refresh_token)

    with pytest.raises(InvalidRefreshTokenError):
        await refresh_use_case.execute(login_result.refresh_token)

    replacement_session = await auth_session_repository.get_by_id(refreshed_claims.token_id)
    assert replacement_session is not None
    assert replacement_session.revoked_at is not None


@pytest.mark.anyio
async def test_logout_session_use_case_revokes_persisted_session() -> None:
    user = _user()
    user_repository = InMemoryUserRepository(users=[user])
    auth_session_repository = InMemoryAuthSessionRepository()
    token_service = JwtTokenService(
        secret_key="test-auth-secret",
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )
    login_use_case = LoginUserUseCase(
        user_repository=user_repository,
        auth_session_repository=auth_session_repository,
        password_hasher=ScryptPasswordHasher(),
        token_service=token_service,
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )
    logout_use_case = LogoutSessionUseCase(
        auth_session_repository=auth_session_repository,
        token_service=token_service,
    )

    login_result = await login_use_case.execute(
        LoginCommand(email="alice@example.com", password="StrongPass123!")
    )
    refresh_claims = token_service.verify_refresh_token(login_result.refresh_token)

    await logout_use_case.execute(login_result.refresh_token)

    auth_session = await auth_session_repository.get_by_id(refresh_claims.token_id)
    assert auth_session is not None
    assert auth_session.revoked_at is not None


@pytest.mark.anyio
async def test_get_authenticated_user_use_case_returns_user_for_valid_token() -> None:
    user = _user()
    repository = InMemoryUserRepository(users=[user])
    token_service = JwtTokenService(
        secret_key="test-auth-secret",
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=86400,
    )
    use_case = GetAuthenticatedUserUseCase(
        user_repository=repository,
        token_service=token_service,
    )

    result = await use_case.execute(token_service.issue_access_token(user.id))

    assert result.id == user.id
    assert result.email == user.email
    assert result.full_name == user.full_name


@pytest.mark.anyio
async def test_get_authenticated_membership_use_case_returns_membership_for_valid_context() -> None:
    user = _user()
    membership = _membership(user.id)
    repository = InMemoryOrganizationMembershipRepository(memberships=[membership])
    use_case = GetAuthenticatedMembershipUseCase(
        organization_membership_repository=repository,
    )

    result = await use_case.execute(
        current_user_id=user.id,
        membership_id=membership.id,
    )

    assert result.id == membership.id
    assert result.organization_id == membership.organization_id
    assert result.user_id == user.id


@pytest.mark.anyio
async def test_get_authenticated_membership_use_case_rejects_foreign_membership() -> None:
    user = _user()
    foreign_membership = _membership(uuid4())
    repository = InMemoryOrganizationMembershipRepository(memberships=[foreign_membership])
    use_case = GetAuthenticatedMembershipUseCase(
        organization_membership_repository=repository,
    )

    with pytest.raises(InvalidMembershipContextError):
        await use_case.execute(
            current_user_id=user.id,
            membership_id=foreign_membership.id,
        )


@pytest.mark.anyio
async def test_list_authenticated_memberships_use_case_returns_active_memberships() -> None:
    user = _user()
    first_organization = _organization("Alpha Industrial", "alpha-industrial")
    second_organization = _organization("Beta Foundry", "beta-foundry")
    first_membership = OrganizationMembership(
        id=uuid4(),
        organization_id=first_organization.id,
        user_id=user.id,
        role=OrganizationMembershipRole.OWNER,
        status=OrganizationMembershipStatus.ACTIVE,
        joined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    second_membership = OrganizationMembership(
        id=uuid4(),
        organization_id=second_organization.id,
        user_id=user.id,
        role=OrganizationMembershipRole.MEMBER,
        status=OrganizationMembershipStatus.ACTIVE,
        joined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    use_case = ListAuthenticatedMembershipsUseCase(
        organization_membership_repository=InMemoryOrganizationMembershipRepository(
            memberships=[first_membership, second_membership]
        ),
        organization_repository=InMemoryOrganizationRepository(
            organizations=[first_organization, second_organization]
        ),
    )

    result = await use_case.execute(
        current_user_id=user.id,
        pagination=PaginationParams(),
    )

    assert len(result.items) == 2
    assert result.items[0].organization_name == "Alpha Industrial"
    assert result.items[1].organization_name == "Beta Foundry"
    assert result.items[0].organization_slug == "alpha-industrial"
    assert result.items[0].status == OrganizationMembershipStatus.ACTIVE


@pytest.mark.anyio
async def test_get_authenticated_membership_use_case_uses_first_active_membership_when_missing_context() -> None:
    user = _user()
    membership = _membership(user.id)
    repository = InMemoryOrganizationMembershipRepository(memberships=[membership])
    use_case = GetAuthenticatedMembershipUseCase(
        organization_membership_repository=repository,
    )

    result = await use_case.execute(
        current_user_id=user.id,
        membership_id=None,
    )

    assert result.id == membership.id
    assert result.organization_id == membership.organization_id


@pytest.mark.anyio
async def test_build_authenticated_session_user_use_case_returns_active_membership_and_organization() -> None:
    user = _user()
    organization = _organization("Gamma Metals", "gamma-metals")
    membership = OrganizationMembership(
        id=uuid4(),
        organization_id=organization.id,
        user_id=user.id,
        role=OrganizationMembershipRole.OWNER,
        status=OrganizationMembershipStatus.ACTIVE,
        joined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    use_case = BuildAuthenticatedSessionUserUseCase(
        authenticated_membership_use_case=GetAuthenticatedMembershipUseCase(
            organization_membership_repository=InMemoryOrganizationMembershipRepository(
                memberships=[membership]
            )
        ),
        organization_repository=InMemoryOrganizationRepository([organization]),
    )

    result = await use_case.execute(
        current_user=AuthenticatedUserReadModel.model_validate(user, from_attributes=True),
        membership_id=None,
    )

    assert result.active_organization is not None
    assert result.active_membership is not None
    assert result.active_organization.name == "Gamma Metals"
    assert result.active_organization.slug == "gamma-metals"
    assert result.active_membership.id == membership.id
    assert result.active_membership.role == OrganizationMembershipRole.OWNER
