from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.customers.entities import Customer
from app.domain.customers.repositories import CustomerRepository
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipNotFoundError,
)
from app.application.requests.commands import TransitionRequestStatusCommand
from app.application.requests.exceptions import (
    InvalidRequestStatusTransitionError,
    RequestMembershipOrganizationMismatchError,
    RequestNotFoundError,
)
from app.application.requests.services import TransitionRequestStatusUseCase
from app.domain.documents.repositories import DocumentRepository
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.domain.request_comments.repositories import RequestCommentRepository
from app.domain.request_status_history.entities import RequestStatusHistoryEntry
from app.domain.request_status_history.repositories import RequestStatusHistoryRepository
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

    async def get_by_id_and_organization(self, request_id, organization_id):
        request = self._requests.get(request_id)
        if request is None or request.organization_id != organization_id:
            return None
        return request

    async def list_by_organization_id(self, organization_id):
        return [
            request
            for request in self._requests.values()
            if request.organization_id == organization_id
        ]

    async def list_by_organization_filters(
        self,
        organization_id,
        *,
        q=None,
        status=None,
        customer_id=None,
        assigned_membership_id=None,
        source=None,
        limit=None,
        offset=0,
    ):
        requests = await self.list_by_organization_id(organization_id)
        if q:
            requests = [request for request in requests if q.lower() in request.title.lower()]
        if status:
            requests = [request for request in requests if request.status == status]
        if customer_id:
            requests = [request for request in requests if request.customer_id == customer_id]
        if assigned_membership_id:
            requests = [
                request
                for request in requests
                if request.assigned_membership_id == assigned_membership_id
            ]
        if source:
            requests = [request for request in requests if request.source == source]
        end = None if limit is None else offset + limit
        return requests[offset:end]

    async def count_by_organization_filters(
        self,
        organization_id,
        *,
        q=None,
        status=None,
        customer_id=None,
        assigned_membership_id=None,
        source=None,
    ):
        requests = await self.list_by_organization_filters(
            organization_id,
            q=q,
            status=status,
            customer_id=customer_id,
            assigned_membership_id=assigned_membership_id,
            source=source,
        )
        return len(requests)

    async def update(self, request: Request) -> Request:
        self._requests[request.id] = request
        return request

    async def update_status(self, request_id, organization_id, new_status, updated_at):
        request = self._requests[request_id]
        if request.organization_id != organization_id:
            raise ValueError(f"Request '{request_id}' was not found.")
        updated_request = Request(
            id=request.id,
            organization_id=request.organization_id,
            title=request.title,
            description=request.description,
            status=new_status,
            source=request.source,
            created_by_membership_id=request.created_by_membership_id,
            assigned_membership_id=request.assigned_membership_id,
            created_at=request.created_at,
            updated_at=updated_at,
            customer_id=request.customer_id,
        )
        self._requests[request_id] = updated_request
        return updated_request

    async def update_assignment(self, request_id, assigned_membership_id, updated_at):
        request = self._requests[request_id]
        updated_request = Request(
            id=request.id,
            organization_id=request.organization_id,
            title=request.title,
            description=request.description,
            status=request.status,
            source=request.source,
            created_by_membership_id=request.created_by_membership_id,
            assigned_membership_id=assigned_membership_id,
            created_at=request.created_at,
            updated_at=updated_at,
            customer_id=request.customer_id,
        )
        self._requests[request_id] = updated_request
        return updated_request


class InMemoryCustomerRepository(CustomerRepository):
    def __init__(self, customers: list[Customer] | None = None) -> None:
        self._customers = {customer.id: customer for customer in customers or []}

    async def add(self, customer: Customer) -> Customer:
        self._customers[customer.id] = customer
        return customer

    async def get_by_id_and_organization(self, customer_id, organization_id):
        customer = self._customers.get(customer_id)
        if customer is None or customer.organization_id != organization_id:
            return None
        return customer

    async def list_by_ids_and_organization(self, customer_ids, organization_id):
        return [
            customer
            for customer_id in customer_ids
            if (customer := self._customers.get(customer_id)) is not None
            and customer.organization_id == organization_id
        ]


class InMemoryRequestActivityRepository(RequestActivityRepository):
    def __init__(self) -> None:
        self.activities: list[RequestActivity] = []

    async def add(self, activity: RequestActivity) -> RequestActivity:
        self.activities.append(activity)
        return activity

    async def list_by_request_id(self, request_id, *, organization_id, limit=None, offset=0):
        activities = [
            activity
            for activity in self.activities
            if activity.request_id == request_id
            and activity.organization_id == organization_id
        ]
        end = None if limit is None else offset + limit
        return activities[offset:end]

    async def count_by_request_id(self, request_id, *, organization_id):
        return sum(
            1
            for activity in self.activities
            if activity.request_id == request_id and activity.organization_id == organization_id
        )


class InMemoryRequestStatusHistoryRepository(RequestStatusHistoryRepository):
    def __init__(self) -> None:
        self.entries: list[RequestStatusHistoryEntry] = []

    async def add(self, entry: RequestStatusHistoryEntry) -> RequestStatusHistoryEntry:
        self.entries.append(entry)
        return entry


class NoOpDocumentRepository(DocumentRepository):
    async def add(self, document):
        return document

    async def get_by_id(self, document_id):
        return None

    async def list_by_request_id(self, request_id, *, organization_id, limit=None, offset=0):
        return []

    async def count_by_request_id(self, request_id, *, organization_id):
        return 0

    async def count_by_request_ids(self, request_ids, *, organization_id):
        return {}

    async def update_processing_status(self, document_id, status, updated_at):
        raise NotImplementedError

    async def update_verified_structured_data(
        self,
        document_id,
        verified_structured_data,
        updated_at,
    ):
        raise NotImplementedError

    async def save_changes(self) -> None:
        return None


class NoOpRequestCommentRepository(RequestCommentRepository):
    async def add(self, comment):
        return comment

    async def list_by_request_id(self, request_id, *, organization_id, limit=None, offset=0):
        return []

    async def count_by_request_id(self, request_id, *, organization_id):
        return 0

    async def count_by_request_ids(self, request_ids, *, organization_id):
        return {}

    async def save_changes(self) -> None:
        return None


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
        assigned_membership_id=None,
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
        status=OrganizationMembershipStatus.ACTIVE,
        joined_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_transition_request_status_use_case_applies_valid_transition() -> None:
    organization_id = uuid4()
    request = _request(organization_id, status=RequestStatus.NEW)
    membership = _membership(organization_id)
    activity_repository = InMemoryRequestActivityRepository()
    status_history_repository = InMemoryRequestStatusHistoryRepository()
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository([request]),
        request_activity_repository=activity_repository,
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_status_history_repository=status_history_repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    result = await use_case.execute(
        request_id=request.id,
        command=TransitionRequestStatusCommand(
            organization_id=organization_id,
            membership_id=membership.id,
            user_id=membership.user_id,
            new_status=RequestStatus.UNDER_REVIEW,
        ),
    )

    assert result.status == RequestStatus.UNDER_REVIEW
    assert len(activity_repository.activities) == 1
    activity = activity_repository.activities[0]
    assert activity.type == RequestActivityType.STATUS_CHANGED
    assert activity.payload["old_status"] == RequestStatus.NEW.value
    assert activity.payload["new_status"] == RequestStatus.UNDER_REVIEW.value
    assert len(status_history_repository.entries) == 1
    history_entry = status_history_repository.entries[0]
    assert history_entry.request_id == request.id
    assert history_entry.organization_id == organization_id
    assert history_entry.previous_status == RequestStatus.NEW
    assert history_entry.new_status == RequestStatus.UNDER_REVIEW
    assert history_entry.changed_by == membership.id
    assert history_entry.changed_by_user_id == membership.user_id


@pytest.mark.anyio
async def test_transition_request_status_use_case_rejects_invalid_transition() -> None:
    organization_id = uuid4()
    request = _request(organization_id, status=RequestStatus.NEW)
    membership = _membership(organization_id)
    use_case = TransitionRequestStatusUseCase(
        request_repository=InMemoryRequestRepository([request]),
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(InvalidRequestStatusTransitionError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=membership.id,
                user_id=membership.user_id,
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(
            request_id=uuid4(),
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=membership.id,
                user_id=membership.user_id,
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(OrganizationMembershipNotFoundError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=uuid4(),
                user_id=uuid4(),
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestMembershipOrganizationMismatchError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=membership.id,
                user_id=membership.user_id,
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization_id,
                membership_id=membership.id,
                user_id=membership.user_id,
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )
