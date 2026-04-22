from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.application.common.exceptions import ValidationError
from app.application.common.pagination import PaginationParams
from app.domain.customers.entities import Customer
from app.domain.customers.repositories import CustomerRepository
from app.application.request_activities.schemas import RequestActivityReadModel
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipNotFoundError,
)
from app.application.organizations.exceptions import OrganizationNotFoundError
from app.application.requests.commands import CreateRequestCommand
from app.application.requests.commands import ListRequestsFilters
from app.application.requests.commands import TransitionRequestStatusCommand
from app.application.requests.commands import UpdateRequestCommand
from app.application.requests.exceptions import (
    InvalidRequestStatusTransitionError,
    RequestCustomerNotFoundError,
    RequestMembershipOrganizationMismatchError,
    RequestNotFoundError,
)
from app.domain.documents.repositories import DocumentRepository
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.domain.request_comments.repositories import RequestCommentRepository
from app.domain.request_status_history.entities import RequestStatusHistoryEntry
from app.domain.request_status_history.repositories import RequestStatusHistoryRepository
from app.application.requests.services import (
    CreateRequestUseCase,
    GetRequestByIdUseCase,
    ListRequestActivitiesUseCase,
    ListRequestsUseCase,
    TransitionRequestStatusUseCase,
    UpdateRequestUseCase,
)
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus
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
    def __init__(self) -> None:
        self._requests: dict[object, Request] = {}

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
        status=OrganizationMembershipStatus.ACTIVE,
        joined_at=now,
        created_at=now,
        updated_at=now,
    )


def _customer(organization_id, name: str = "Acme Customer") -> Customer:
    now = datetime.now(UTC)
    return Customer(
        id=uuid4(),
        organization_id=organization_id,
        name=name,
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        organization_repository=InMemoryOrganizationRepository([organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        customer_repository=InMemoryCustomerRepository(),
    )

    result = await use_case.execute(
        organization.id,
        CreateRequestCommand(
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        organization_repository=InMemoryOrganizationRepository([organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(OrganizationMembershipNotFoundError):
        await use_case.execute(
            organization.id,
            CreateRequestCommand(
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        organization_repository=InMemoryOrganizationRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(OrganizationNotFoundError):
        await use_case.execute(
            organization.id,
            CreateRequestCommand(
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        organization_repository=InMemoryOrganizationRepository([organization, other_organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestMembershipOrganizationMismatchError):
        await use_case.execute(
            organization.id,
            CreateRequestCommand(
                title="Cross org membership",
                description=None,
                source=RequestSource.WEB_FORM,
                created_by_membership_id=membership.id,
            )
        )


@pytest.mark.anyio
async def test_create_request_use_case_accepts_customer_from_same_organization() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    customer = _customer(organization.id)
    request_repository = InMemoryRequestRepository()
    use_case = CreateRequestUseCase(
        request_repository=request_repository,
        request_activity_repository=InMemoryRequestActivityRepository(),
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        organization_repository=InMemoryOrganizationRepository([organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        customer_repository=InMemoryCustomerRepository([customer]),
    )

    result = await use_case.execute(
        organization.id,
        CreateRequestCommand(
            title="Customer-linked request",
            description="Validated against same tenant",
            source=RequestSource.MANUAL,
            created_by_membership_id=membership.id,
            customer_id=customer.id,
        ),
    )

    stored_request = await request_repository.get_by_id(result.id)

    assert result.organization_id == organization.id
    assert result.customer_id == customer.id
    assert stored_request is not None
    assert stored_request.organization_id == organization.id
    assert stored_request.customer_id == customer.id


@pytest.mark.anyio
async def test_create_request_use_case_rejects_missing_customer() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    use_case = CreateRequestUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=InMemoryRequestActivityRepository(),
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        organization_repository=InMemoryOrganizationRepository([organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestCustomerNotFoundError):
        await use_case.execute(
            organization.id,
            CreateRequestCommand(
                title="Missing customer",
                description=None,
                source=RequestSource.API,
                created_by_membership_id=membership.id,
                customer_id=uuid4(),
            ),
        )


@pytest.mark.anyio
async def test_create_request_use_case_rejects_customer_from_other_organization() -> None:
    organization = _organization(name="Alpha Org", slug="alpha-org")
    other_organization = _organization(name="Beta Org", slug="beta-org")
    membership = _membership(organization.id)
    foreign_customer = _customer(other_organization.id, name="Foreign Customer")
    use_case = CreateRequestUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=InMemoryRequestActivityRepository(),
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        organization_repository=InMemoryOrganizationRepository([organization, other_organization]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        customer_repository=InMemoryCustomerRepository([foreign_customer]),
    )

    with pytest.raises(RequestCustomerNotFoundError):
        await use_case.execute(
            organization.id,
            CreateRequestCommand(
                title="Cross org customer",
                description=None,
                source=RequestSource.WEB_FORM,
                created_by_membership_id=membership.id,
                customer_id=foreign_customer.id,
            ),
        )


@pytest.mark.anyio
async def test_list_requests_use_case_returns_only_requests_from_current_tenant() -> None:
    organization = _organization(name="Tenant One", slug="tenant-one")
    other_organization = _organization(name="Tenant Two", slug="tenant-two")
    membership = _membership(organization.id)
    customer = _customer(organization.id, name="Acme Components")
    repository = InMemoryRequestRepository()
    own_request = Request(
        id=uuid4(),
        organization_id=organization.id,
        customer_id=customer.id,
        title="Own tenant request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    foreign_request = Request(
        id=uuid4(),
        organization_id=other_organization.id,
        title="Foreign tenant request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=uuid4(),
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    use_case = ListRequestsUseCase(
        request_repository=repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository([customer]),
    )
    await repository.add(own_request)
    await repository.add(foreign_request)

    result = await use_case.execute(
        organization.id,
        ListRequestsFilters(),
        PaginationParams(),
    )

    assert [item.id for item in result.items] == [own_request.id]
    assert result.items[0].customer_id == customer.id
    assert result.items[0].customer is not None
    assert result.items[0].customer.id == customer.id
    assert result.items[0].customer.name == "Acme Components"


@pytest.mark.anyio
async def test_list_requests_use_case_supports_customer_id_filter_within_tenant() -> None:
    organization = _organization(name="Tenant Filter Org", slug="tenant-filter-org")
    membership = _membership(organization.id)
    target_customer = _customer(organization.id, name="Target Customer")
    other_customer = _customer(organization.id, name="Other Customer")
    repository = InMemoryRequestRepository()
    target_request = Request(
        id=uuid4(),
        organization_id=organization.id,
        customer_id=target_customer.id,
        title="Target customer request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.API,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    other_request = Request(
        id=uuid4(),
        organization_id=organization.id,
        customer_id=other_customer.id,
        title="Other customer request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.API,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    use_case = ListRequestsUseCase(
        request_repository=repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository([target_customer, other_customer]),
    )
    await repository.add(target_request)
    await repository.add(other_request)

    result = await use_case.execute(
        organization.id,
        ListRequestsFilters(customer_id=target_customer.id),
        PaginationParams(),
    )

    assert [item.id for item in result.items] == [target_request.id]
    assert result.items[0].customer is not None
    assert result.items[0].customer.id == target_customer.id
    assert result.items[0].customer.name == "Target Customer"


@pytest.mark.anyio
async def test_list_requests_use_case_combines_status_and_customer_filters_safely() -> None:
    organization = _organization(name="Tenant Combined Org", slug="tenant-combined-org")
    other_organization = _organization(name="Foreign Combined Org", slug="foreign-combined-org")
    membership = _membership(organization.id)
    local_customer = _customer(organization.id, name="Local Customer")
    foreign_customer = _customer(other_organization.id, name="Foreign Customer")
    repository = InMemoryRequestRepository()
    matching_request = Request(
        id=uuid4(),
        organization_id=organization.id,
        customer_id=local_customer.id,
        title="Matching request",
        description=None,
        status=RequestStatus.UNDER_REVIEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    wrong_status_request = Request(
        id=uuid4(),
        organization_id=organization.id,
        customer_id=local_customer.id,
        title="Wrong status request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    foreign_request = Request(
        id=uuid4(),
        organization_id=other_organization.id,
        customer_id=foreign_customer.id,
        title="Foreign matching request",
        description=None,
        status=RequestStatus.UNDER_REVIEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=uuid4(),
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    use_case = ListRequestsUseCase(
        request_repository=repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository([local_customer, foreign_customer]),
    )
    await repository.add(matching_request)
    await repository.add(wrong_status_request)
    await repository.add(foreign_request)

    result = await use_case.execute(
        organization.id,
        ListRequestsFilters(
            status=RequestStatus.UNDER_REVIEW,
            customer_id=local_customer.id,
        ),
        PaginationParams(),
    )

    assert [item.id for item in result.items] == [matching_request.id]
    assert result.items[0].organization_id == organization.id
    assert result.items[0].customer_id == local_customer.id


@pytest.mark.anyio
async def test_get_request_by_id_use_case_returns_request_from_same_tenant() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    customer = _customer(organization.id, name="Scoped Customer")
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        customer_id=customer.id,
        title="Tenant request",
        description="Scoped read",
        status=RequestStatus.NEW,
        source=RequestSource.API,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository = InMemoryRequestRepository()
    await repository.add(request)
    use_case = GetRequestByIdUseCase(
        request_repository=repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository([customer]),
    )

    result = await use_case.execute(request.id, organization.id)

    assert result.id == request.id
    assert result.organization_id == organization.id
    assert result.customer is not None
    assert result.customer.id == customer.id
    assert result.customer.name == "Scoped Customer"


@pytest.mark.anyio
async def test_get_request_by_id_use_case_rejects_missing_request() -> None:
    use_case = GetRequestByIdUseCase(
        request_repository=InMemoryRequestRepository(),
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(uuid4(), uuid4())


@pytest.mark.anyio
async def test_get_request_by_id_use_case_rejects_request_from_other_tenant() -> None:
    organization = _organization(name="Tenant One", slug="tenant-one")
    other_organization = _organization(name="Tenant Two", slug="tenant-two")
    foreign_request = Request(
        id=uuid4(),
        organization_id=other_organization.id,
        title="Foreign tenant request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.WEB_FORM,
        created_by_membership_id=uuid4(),
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository = InMemoryRequestRepository()
    await repository.add(foreign_request)
    use_case = GetRequestByIdUseCase(
        request_repository=repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(foreign_request.id, organization.id)


@pytest.mark.anyio
async def test_list_request_activities_use_case_returns_ordered_timeline_for_tenant() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    now = datetime.now(UTC)
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        title="Timeline request",
        description="Track timeline",
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=now,
        updated_at=now,
    )
    activity_repository = InMemoryRequestActivityRepository()
    activity_repository.activities.extend(
        [
            RequestActivity(
                id=uuid4(),
                request_id=request.id,
                organization_id=organization.id,
                membership_id=membership.id,
                type=RequestActivityType.REQUEST_CREATED,
                payload={"request_id": str(request.id), "title": request.title},
                created_at=now,
            ),
            RequestActivity(
                id=uuid4(),
                request_id=request.id,
                organization_id=organization.id,
                membership_id=membership.id,
                type=RequestActivityType.REQUEST_UPDATED,
                payload={
                    "request_id": str(request.id),
                    "actor_user_id": str(membership.user_id),
                    "updated_fields": ["title"],
                },
                created_at=now + timedelta(microseconds=1),
            ),
            RequestActivity(
                id=uuid4(),
                request_id=request.id,
                organization_id=uuid4(),
                membership_id=membership.id,
                type=RequestActivityType.REQUEST_UPDATED,
                payload={"request_id": str(request.id), "updated_fields": ["description"]},
                created_at=now + timedelta(microseconds=2),
            ),
        ]
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    use_case = ListRequestActivitiesUseCase(
        request_repository=request_repository,
        request_activity_repository=activity_repository,
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
    )

    result = await use_case.execute(request.id, organization.id, PaginationParams())

    assert [activity.type for activity in result.items] == [
        RequestActivityType.REQUEST_CREATED,
        RequestActivityType.REQUEST_UPDATED,
    ]
    assert result.items[0].actor.membership_id == membership.id
    assert result.items[0].actor.user_id == membership.user_id
    assert result.items[0].metadata["title"] == request.title
    assert result.items[1].membership_id == membership.id
    assert result.items[1].actor.membership_id == membership.id
    assert result.items[1].actor.user_id == membership.user_id
    assert result.items[1].metadata["updated_fields"] == ["title"]
    assert result.items[1].payload["actor_user_id"] == str(membership.user_id)


@pytest.mark.anyio
async def test_list_request_activities_use_case_rejects_request_from_other_tenant() -> None:
    organization = _organization(name="Timeline Tenant One", slug="timeline-tenant-one")
    other_organization = _organization(name="Timeline Tenant Two", slug="timeline-tenant-two")
    request = Request(
        id=uuid4(),
        organization_id=other_organization.id,
        title="Foreign timeline request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.API,
        created_by_membership_id=uuid4(),
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    use_case = ListRequestActivitiesUseCase(
        request_repository=request_repository,
        request_activity_repository=InMemoryRequestActivityRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(request.id, organization.id, PaginationParams())


@pytest.mark.anyio
async def test_update_request_use_case_updates_editable_fields_within_same_tenant() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    original_customer = _customer(organization.id, name="Original Customer")
    updated_customer = _customer(organization.id, name="Updated Customer")
    now = datetime.now(UTC)
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        title="Original title",
        description="Original description",
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=now,
        updated_at=now,
        customer_id=original_customer.id,
    )
    repository = InMemoryRequestRepository()
    await repository.add(request)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = UpdateRequestUseCase(
        request_repository=repository,
        request_activity_repository=activity_repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository([original_customer, updated_customer]),
    )

    result = await use_case.execute(
        request_id=request.id,
        organization_id=organization.id,
        command=UpdateRequestCommand(
            title="Updated title",
            description="Updated description",
            customer_id=updated_customer.id,
            membership_id=membership.id,
            user_id=membership.user_id,
        ),
    )

    stored_request = await repository.get_by_id(request.id)

    assert result.id == request.id
    assert result.organization_id == organization.id
    assert result.title == "Updated title"
    assert result.description == "Updated description"
    assert result.customer_id == updated_customer.id
    assert stored_request is not None
    assert stored_request.customer_id == updated_customer.id
    assert stored_request.updated_at > request.updated_at
    assert len(activity_repository.activities) == 1
    activity = activity_repository.activities[0]
    assert activity.request_id == request.id
    assert activity.organization_id == organization.id
    assert activity.membership_id == membership.id
    assert activity.type == RequestActivityType.REQUEST_UPDATED
    assert activity.payload["request_id"] == str(request.id)
    assert activity.payload["actor_user_id"] == str(membership.user_id)
    assert activity.payload["updated_fields"] == [
        "title",
        "description",
        "customer_id",
    ]


@pytest.mark.anyio
async def test_update_request_use_case_rejects_missing_request() -> None:
    activity_repository = InMemoryRequestActivityRepository()
    use_case = UpdateRequestUseCase(
        request_repository=InMemoryRequestRepository(),
        request_activity_repository=activity_repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(
            request_id=uuid4(),
            organization_id=uuid4(),
            command=UpdateRequestCommand(
                title="Updated title",
                membership_id=uuid4(),
                user_id=uuid4(),
            ),
        )
    assert activity_repository.activities == []


@pytest.mark.anyio
async def test_update_request_use_case_rejects_request_from_other_tenant() -> None:
    organization = _organization(name="Tenant One", slug="tenant-one")
    other_organization = _organization(name="Tenant Two", slug="tenant-two")
    request = Request(
        id=uuid4(),
        organization_id=other_organization.id,
        title="Foreign request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.WEB_FORM,
        created_by_membership_id=uuid4(),
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository = InMemoryRequestRepository()
    await repository.add(request)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = UpdateRequestUseCase(
        request_repository=repository,
        request_activity_repository=activity_repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(
            request_id=request.id,
            organization_id=organization.id,
            command=UpdateRequestCommand(
                title="Should fail",
                membership_id=uuid4(),
                user_id=uuid4(),
            ),
        )
    assert activity_repository.activities == []


@pytest.mark.anyio
async def test_update_request_use_case_rejects_customer_from_other_tenant() -> None:
    organization = _organization(name="Tenant One", slug="tenant-one")
    other_organization = _organization(name="Tenant Two", slug="tenant-two")
    membership = _membership(organization.id)
    foreign_customer = _customer(other_organization.id, name="Foreign Customer")
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        title="Tenant request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.MANUAL,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository = InMemoryRequestRepository()
    await repository.add(request)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = UpdateRequestUseCase(
        request_repository=repository,
        request_activity_repository=activity_repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository([foreign_customer]),
    )

    with pytest.raises(RequestCustomerNotFoundError):
        await use_case.execute(
            request_id=request.id,
            organization_id=organization.id,
            command=UpdateRequestCommand(
                customer_id=foreign_customer.id,
                membership_id=membership.id,
                user_id=membership.user_id,
            ),
        )
    assert activity_repository.activities == []


@pytest.mark.anyio
async def test_update_request_use_case_rejects_empty_payload() -> None:
    organization = _organization()
    membership = _membership(organization.id)
    request = Request(
        id=uuid4(),
        organization_id=organization.id,
        title="Tenant request",
        description=None,
        status=RequestStatus.NEW,
        source=RequestSource.API,
        created_by_membership_id=membership.id,
        assigned_membership_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository = InMemoryRequestRepository()
    await repository.add(request)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = UpdateRequestUseCase(
        request_repository=repository,
        request_activity_repository=activity_repository,
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(ValidationError):
        await use_case.execute(
            request_id=request.id,
            organization_id=organization.id,
            command=UpdateRequestCommand(
                membership_id=membership.id,
                user_id=membership.user_id,
            ),
        )
    assert activity_repository.activities == []


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
        assigned_membership_id=None,
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    activity_repository = InMemoryRequestActivityRepository()
    status_history_repository = InMemoryRequestStatusHistoryRepository()
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
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
            organization_id=organization.id,
            membership_id=membership.id,
            user_id=membership.user_id,
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
    assert len(status_history_repository.entries) == 1
    history_entry = status_history_repository.entries[0]
    assert history_entry.request_id == request.id
    assert history_entry.organization_id == organization.id
    assert history_entry.previous_status == RequestStatus.NEW
    assert history_entry.new_status == RequestStatus.UNDER_REVIEW
    assert history_entry.changed_by == membership.id
    assert history_entry.changed_by_user_id == membership.user_id


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
        assigned_membership_id=None,
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(InvalidRequestStatusTransitionError):
        await use_case.execute(
            request_id=request.id,
            command=TransitionRequestStatusCommand(
                organization_id=organization.id,
                membership_id=membership.id,
                user_id=membership.user_id,
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
        request_status_history_repository=InMemoryRequestStatusHistoryRepository(),
        document_repository=NoOpDocumentRepository(),
        request_comment_repository=NoOpRequestCommentRepository(),
        customer_repository=InMemoryCustomerRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(
            request_id=uuid4(),
            command=TransitionRequestStatusCommand(
                organization_id=organization.id,
                membership_id=membership.id,
                user_id=membership.user_id,
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
        assigned_membership_id=None,
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
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
                organization_id=organization.id,
                membership_id=uuid4(),
                user_id=uuid4(),
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
        assigned_membership_id=None,
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
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
                organization_id=organization.id,
                membership_id=membership.id,
                user_id=membership.user_id,
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
        assigned_membership_id=None,
        created_at=now,
        updated_at=now,
    )
    request_repository = InMemoryRequestRepository()
    await request_repository.add(request)
    use_case = TransitionRequestStatusUseCase(
        request_repository=request_repository,
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
                organization_id=organization.id,
                membership_id=membership.id,
                user_id=membership.user_id,
                new_status=RequestStatus.UNDER_REVIEW,
            ),
        )
