from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.organization_memberships.commands import CreateOrganizationMembershipCommand
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipAlreadyExistsError,
)
from app.application.organization_memberships.services import (
    CreateOrganizationMembershipUseCase,
)
from app.application.organizations.exceptions import OrganizationNotFoundError
from app.application.users.exceptions import UserNotFoundError
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus
from app.domain.organizations.entities import Organization
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.users.entities import User
from app.domain.users.repositories import UserRepository


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


class InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[User] | None = None) -> None:
        self._users = {user.id: user for user in users or []}

    async def add(self, user: User) -> User:
        self._users[user.id] = user
        return user

    async def get_by_id(self, user_id):
        return self._users.get(user_id)

    async def get_by_email(self, email: str):
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def list_by_ids(self, user_ids):
        return [
            user
            for user_id in user_ids
            if (user := self._users.get(user_id)) is not None
        ]


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
        end = None if limit is None else offset + limit
        return memberships[offset:end]

    async def count_active_by_user_id(self, user_id):
        return sum(
            1
            for membership in self._memberships.values()
            if membership.user_id == user_id and membership.is_active
        )

    async def list_active_by_organization_id(self, organization_id, *, limit=None, offset=0):
        memberships = [
            membership
            for membership in self._memberships.values()
            if membership.organization_id == organization_id and membership.is_active
        ]
        end = None if limit is None else offset + limit
        return memberships[offset:end]

    async def list_by_organization_id(self, organization_id, *, limit=None, offset=0):
        memberships = [
            membership
            for membership in self._memberships.values()
            if membership.organization_id == organization_id
        ]
        end = None if limit is None else offset + limit
        return memberships[offset:end]

    async def count_by_organization_id(self, organization_id):
        return sum(
            1
            for membership in self._memberships.values()
            if membership.organization_id == organization_id
        )

    async def list_by_ids_and_organization(self, membership_ids, organization_id):
        return [
            membership
            for membership_id in membership_ids
            if (membership := self._memberships.get(membership_id)) is not None
            and membership.organization_id == organization_id
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


def _organization() -> Organization:
    now = datetime.now(UTC)
    return Organization(
        id=uuid4(),
        name="Factory Org",
        slug="factory-org",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="member@example.com",
        full_name="Member Example",
        password_hash=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "role",
    [
        OrganizationMembershipRole.OWNER,
        OrganizationMembershipRole.ADMIN,
        OrganizationMembershipRole.MEMBER,
    ],
)
async def test_create_organization_membership_use_case_creates_active_membership(
    role: OrganizationMembershipRole,
) -> None:
    organization = _organization()
    user = _user()
    use_case = CreateOrganizationMembershipUseCase(
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
        organization_repository=InMemoryOrganizationRepository([organization]),
        user_repository=InMemoryUserRepository([user]),
    )

    result = await use_case.execute(
        CreateOrganizationMembershipCommand(
            organization_id=organization.id,
            user_id=user.id,
            role=role,
        )
    )

    assert result.organization_id == organization.id
    assert result.user_id == user.id
    assert result.role == role
    assert result.is_active is True
    assert result.status == OrganizationMembershipStatus.ACTIVE
    assert result.joined_at is not None


@pytest.mark.anyio
async def test_create_organization_membership_use_case_rejects_duplicate_active_membership() -> None:
    organization = _organization()
    user = _user()
    now = datetime.now(UTC)
    existing_membership = OrganizationMembership(
        id=uuid4(),
        organization_id=organization.id,
        user_id=user.id,
        role=OrganizationMembershipRole.MEMBER,
        status=OrganizationMembershipStatus.ACTIVE,
        joined_at=now,
        created_at=now,
        updated_at=now,
    )
    use_case = CreateOrganizationMembershipUseCase(
        organization_membership_repository=InMemoryOrganizationMembershipRepository(
            [existing_membership]
        ),
        organization_repository=InMemoryOrganizationRepository([organization]),
        user_repository=InMemoryUserRepository([user]),
    )

    with pytest.raises(OrganizationMembershipAlreadyExistsError):
        await use_case.execute(
            CreateOrganizationMembershipCommand(
                organization_id=organization.id,
                user_id=user.id,
                role=OrganizationMembershipRole.ADMIN,
            )
        )


@pytest.mark.anyio
async def test_create_organization_membership_use_case_rejects_missing_organization() -> None:
    user = _user()
    use_case = CreateOrganizationMembershipUseCase(
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
        organization_repository=InMemoryOrganizationRepository(),
        user_repository=InMemoryUserRepository([user]),
    )

    with pytest.raises(OrganizationNotFoundError):
        await use_case.execute(
            CreateOrganizationMembershipCommand(
                organization_id=uuid4(),
                user_id=user.id,
                role=OrganizationMembershipRole.MEMBER,
            )
        )


@pytest.mark.anyio
async def test_create_organization_membership_use_case_rejects_missing_user() -> None:
    organization = _organization()
    use_case = CreateOrganizationMembershipUseCase(
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
        organization_repository=InMemoryOrganizationRepository([organization]),
        user_repository=InMemoryUserRepository(),
    )

    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            CreateOrganizationMembershipCommand(
                organization_id=organization.id,
                user_id=uuid4(),
                role=OrganizationMembershipRole.MEMBER,
            )
        )


def test_create_organization_membership_command_rejects_invalid_role() -> None:
    with pytest.raises(ValidationError):
        CreateOrganizationMembershipCommand(
            organization_id=uuid4(),
            user_id=uuid4(),
            role="SUPERUSER",
        )
