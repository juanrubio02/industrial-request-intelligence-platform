from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.organization_memberships.exceptions import (
    OrganizationMembershipNotFoundError,
)
from app.application.requests.commands import TransitionRequestStatusCommand
from app.application.requests.exceptions import (
    InvalidRequestStatusTransitionError,
    RequestMembershipOrganizationMismatchError,
    RequestNotFoundError,
    RequestOrganizationMismatchError,
)
from app.application.requests.services import TransitionRequestStatusUseCase
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.domain.requests.entities import Request
from app.domain.requests.repositories import RequestRepository
from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


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
    def __init__(self, requests: list[Request] | None = None) -> None:
        self._requests = {request.id: request for request in requests or []}

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


def _request(organization_id, status: RequestStatus = RequestStatus.NEW) -> Request:
    now = datetime.now(UTC)
    return Request(
        id=uuid4(),
        organization_id=organization_id,
        title="Need valves",
        description="Request details",
        status=status,
        source=RequestSource.EMAIL,
        created_by_membership_id=uuid4(),
        created_at=now,
        updated_at=now,
    )


def _membership(organization_id) -> OrganizationMembership:
    now = datetime.now(UTC)
    return OrganizationMembership(
        id=uuid4(),
        organization_id=organization_id,
        user_id=uuid4(),
        role=OrganizationMembershipRole.ADMIN,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_transition_request_status_use_case_applies_valid_transition() -> None:
    organization_id = uuid4()
    request = _request(organization_id, status=RequestStatus.NEW)
    membership = _membership(organization_id)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository([request]),
        request_activity_repository=activity_repository,
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    result = await use_case.execute(
        request_id=request.id,
        command=TransitionRequestStatusCommand(
            organization_id=organization_id,
            membership_id=membership.id,
            new_status=RequestStatus.UNDER_REVIEW,
        ),
    )

    assert result.status == RequestStatus.UNDER_REVIEW
    assert len(activity_repository.activities) == 1
    activity = activity_repository.activities[0]
    assert activity.type == RequestActivityType.STATUS_CHANGED
    assert activity.payload["old_status"] == RequestStatus.NEW.value
    assert activity.payload["new_status"] == RequestStatus.UNDER_REVIEW.value


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_invalid_transition() -> None:
    organization_id = uuid4()
    request = _request(organization_id, status=RequestStatus.NEW)
    membership = _membership(organization_id)
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository([request]),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(InvalidRequestStatusTransitionError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=membership.id,
                new_status=RequestStatus.WON,
            ),
        )


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_missing_request() -> None:
    organization_id = uuid4()
    membership = _membership(organization_id)
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(
            request_id=uuid4(),
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=membership.id,
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_missing_membership() -> None:
    organization_id = uuid4()
    request = _request(organization_id)
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository([request]),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
    )

    with pytest.raises(OrganizationMembershipNotFoundError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=uuid4(),
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_membership_from_other_organization() -> None:
    organization_id = uuid4()
    request = _request(organization_id)
    membership = _membership(uuid4())
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository([request]),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(RequestMembershipOrganizationMismatchError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=membership.id,
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_request_from_other_organization() -> None:
    organization_id = uuid4()
    request = _request(uuid4())
    membership = _membership(organization_id)
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository([request]),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    with pytest.raises(RequestOrganizationMismatchError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=membership.id,
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )
