from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.auth.commands import LoginCommand
from app.application.auth.exceptions import (
    InvalidCredentialsError,
    InvalidMembershipContextError,
)
from app.application.auth.services import (
    GetAuthenticatedMembershipUseCase,
    GetAuthenticatedUserUseCase,
    ListAuthenticatedMembershipsUseCase,
    LoginUserUseCase,
)
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organizations.entities import Organization
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.users.entities import User
from app.domain.users.repositories import UserRepository
from app.infrastructure.auth.password import ScryptPasswordHasher
from app.infrastructure.auth.tokens import HmacAccessTokenService


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

    async def list_active_by_user_id(self, user_id):
        return [
            membership
            for membership in self._memberships.values()
            if membership.user_id == user_id and membership.is_active
        ]


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
        is_active=is_active,
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
async def test_login_user_use_case_returns_access_token_for_valid_credentials() -> None:
    repository = InMemoryUserRepository(users=[_user()])
    use_case = LoginUserUseCase(
        user_repository=repository,
        password_hasher=ScryptPasswordHasher(),
        access_token_service=HmacAccessTokenService(
            secret_key="test-auth-secret",
            ttl_seconds=3600,
        ),
    )

    result = await use_case.execute(
        LoginCommand(email="alice@example.com", password="StrongPass123!")
    )

    assert result.token_type == "bearer"
    assert result.access_token


@pytest.mark.anyio
async def test_login_user_use_case_rejects_invalid_credentials() -> None:
    repository = InMemoryUserRepository(users=[_user()])
    use_case = LoginUserUseCase(
        user_repository=repository,
        password_hasher=ScryptPasswordHasher(),
        access_token_service=HmacAccessTokenService(
            secret_key="test-auth-secret",
            ttl_seconds=3600,
        ),
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginCommand(email="alice@example.com", password="WrongPass123!")
        )


@pytest.mark.anyio
async def test_get_authenticated_user_use_case_returns_user_for_valid_token() -> None:
    user = _user()
    repository = InMemoryUserRepository(users=[user])
    access_token_service = HmacAccessTokenService(
        secret_key="test-auth-secret",
        ttl_seconds=3600,
    )
    use_case = GetAuthenticatedUserUseCase(
        user_repository=repository,
        access_token_service=access_token_service,
    )

    result = await use_case.execute(access_token_service.issue(user.id))

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
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    second_membership = OrganizationMembership(
        id=uuid4(),
        organization_id=second_organization.id,
        user_id=user.id,
        role=OrganizationMembershipRole.MEMBER,
        is_active=True,
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

    result = await use_case.execute(current_user_id=user.id)

    assert len(result) == 2
    assert result[0].organization_name == "Alpha Industrial"
    assert result[1].organization_name == "Beta Foundry"
