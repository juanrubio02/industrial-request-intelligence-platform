from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.request_activities.schemas import RequestActivityReadModel
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipNotFoundError,
)
from app.application.organizations.exceptions import OrganizationNotFoundError
from app.application.requests.commands import CreateRequestCommand
from app.application.requests.commands import TransitionRequestStatusCommand
from app.application.requests.exceptions import (
    InvalidRequestStatusTransitionError,
    RequestMembershipOrganizationMismatchError,
    RequestNotFoundError,
    RequestOrganizationMismatchError,
)
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.application.requests.services import CreateRequestUseCase, TransitionRequestStatusUseCase
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organizations.entities import Organization
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.requests.entities import Request
from app.domain.requests.repositories import RequestRepository
from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


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


class InMemoryRequestRepository(RequestRepository):
    def __init__(self) -> None:
        self._requests: dict[object, Request] = {}

    async def add(self, request: Request) -> Request:
        self._requests[request.id] = request
        return request

    async def save_changes(self) -> None:
        return None

    async def get_by_id(self, request_id):
        return self._requests.get(request_id)

    async def list_by_organization_id(self, organization_id):
        return [
            request
            for request in self._requests.values()
            if request.organization_id == organization_id
        ]

    async def update_status(self, request_id, new_status, updated_at):
        request = self._requests[request_id]
        updated_request = Request(
            id=request.id,
            organization_id=request.organization_id,
            title=request.title,
            description=request.description,
            status=new_status,
            source=request.source,
            created_by_membership_id=request.created_by_membership_id,
            created_at=request.created_at,
            updated_at=updated_at,
        )
        self._requests[request_id] = updated_request
        return updated_request


class InMemoryRequestActivityRepository(RequestActivityRepository):
    def __init__(self) -> None:
        self.activities: list[RequestActivity] = []

    async def add(self, activity: RequestActivity) -> RequestActivity:
        self.activities.append(activity)
        return activity

    async def list_by_request_id(self, request_id):
        return [activity for activity in self.activities if activity.request_id == request_id]


def _organization(name: str = "Acme Org", slug: str = "acme-org") -> Organization:
    now = datetime.now(UTC)
    return Organization(
        id=uuid4(),
        name=name,
        slug=slug,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _membership(organization_id, role: OrganizationMembershipRole = OrganizationMembershipRole.ADMIN):
    now = datetime.now(UTC)
    return OrganizationMembership(
        id=uuid4(),
        organization_id=organization_id,
        user_id=uuid4(),
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_create_request_use_case_creates_request_with_initial_status() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = CreateRequestUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=activity_repository,
        organization_repository=InMemoryOrganizationRepository([organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    result = await use_case.execute(
        CreateRequestCommand(
            organization_id=organization.id,
            title="Need industrial valves",
            description="Urgent replacement for line A",
            source=RequestSource.EMAIL,
            created_by_membership_id=membership.id,
        )
    )

    assert result.organization_id == organization.id
    assert result.created_by_membership_id == membership.id
    assert result.title == "Need industrial valves"
    assert result.description == "Urgent replacement for line A"
    assert result.source == RequestSource.EMAIL
    assert result.status == RequestStatus.NEW
    assert len(activity_repository.activities) == 1
    activity = activity_repository.activities[0]
    assert activity.request_id == result.id
    assert activity.organization_id == organization.id
    assert activity.membership_id == membership.id
    assert activity.type == RequestActivityType.REQUEST_CREATED
    assert activity.payload["status"] == RequestStatus.NEW.value


@pytest.mark.anyio
async def test_create_request_use_case_rejects_missing_membership() -> None:
    organization = _organization()
    use_case = CreateRequestUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_repository=InMemoryOrganizationRepository([organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
    )

    with pytest.raises(OrganizationMembershipNotFoundError):
        await use_case.execute(
            CreateRequestCommand(
                organization_id=organization.id,
                title="Missing membership",
                description=None,
                source=RequestSource.MANUAL,
                created_by_membership_id=uuid4(),
            )
        )


@pytest.mark.anyio
async def test_create_request_use_case_rejects_missing_organization() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    use_case = CreateRequestUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_repository=InMemoryOrganizationRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(OrganizationNotFoundError):
        await use_case.execute(
            CreateRequestCommand(
                organization_id=organization.id,
                title="Missing organization",
                description=None,
                source=RequestSource.API,
                created_by_membership_id=membership.id,
            )
        )


@pytest.mark.anyio
async def test_create_request_use_case_rejects_membership_from_other_organization() -> None:
    organization = _organization(name="Alpha Org", slug="alpha-org")
    other_organization = _organization(name="Beta Org", slug="beta-org")
    membership = _membership(other_organization.id)
    use_case = CreateRequestUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_repository=InMemoryOrganizationRepository([organization, other_organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(RequestMembershipOrganizationMismatchError):
        await use_case.execute(
            CreateRequestCommand(
                organization_id=organization.id,
                title="Cross org membership",
                description=None,
                source=RequestSource.WEB_FORM,
                created_by_membership_id=membership.id,
            )
        )


@pytest.mark.anyio
async def test_transition_request_status_use_case_updates_request_and_creates_activity() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    now = datetime.now(UTC)
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        title="Need industrial valves",
        description="Initial request",
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=membership.id,
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
        request_activity_repository=activity_repository,
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    result = await use_case.execute(
        request_id=request.id,
        command=TransitionRequestStatusCommand(
            organization_id=organization.id,
            membership_id=membership.id,
            new_status=RequestStatus.UNDER_REVIEW,
        ),
    )

    assert result.id == request.id
    assert result.status == RequestStatus.UNDER_REVIEW
    assert len(activity_repository.activities) == 1
    activity = activity_repository.activities[0]
    assert activity.request_id == request.id
    assert activity.organization_id == organization.id
    assert activity.membership_id == membership.id
    assert activity.type == RequestActivityType.STATUS_CHANGED
    assert activity.payload["old_status"] == RequestStatus.NEW.value
    assert activity.payload["new_status"] == RequestStatus.UNDER_REVIEW.value


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_invalid_transition() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    now = datetime.now(UTC)
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        title="Need industrial valves",
        description="Initial request",
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=membership.id,
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
        request_activity_repository=activity_repository,
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(InvalidRequestStatusTransitionError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization.id,
                membership_id=membership.id,
                new_status=RequestStatus.WON,
            ),
        )

    assert len(activity_repository.activities) == 0


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_missing_request() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(
            request_id=uuid4(),
            command=TransitionRequestStatusCommand(
                organization_id=organization.id,
                membership_id=membership.id,
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_missing_membership() -> None:
    organization = _organization()
    now = datetime.now(UTC)
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        title="Need industrial valves",
        description="Initial request",
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=uuid4(),
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
    )

    with pytest.raises(OrganizationMembershipNotFoundError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization.id,
                membership_id=uuid4(),
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_membership_from_other_organization() -> None:
    organization = _organization(name="Alpha Org", slug="alpha-org-transition")
    other_organization = _organization(name="Beta Org", slug="beta-org-transition")
    membership = _membership(other_organization.id)
    now = datetime.now(UTC)
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        title="Need industrial valves",
        description="Initial request",
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=uuid4(),
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(RequestMembershipOrganizationMismatchError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization.id,
                membership_id=membership.id,
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_request_from_other_organization() -> None:
    organization = _organization(name="Gamma Org", slug="gamma-org-transition")
    other_organization = _organization(name="Delta Org", slug="delta-org-transition")
    membership = _membership(organization.id)
    now = datetime.now(UTC)
    request = Request(
        id=uuid4(),
        organization_id=other_organization.id,
        title="Need industrial valves",
        description="Initial request",
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=membership.id,
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(RequestOrganizationMismatchError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization.id,
                membership_id=membership.id,
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )
