from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus
from app.infrastructure.database.models.customer import CustomerModel
from app.infrastructure.database.models.request import RequestModel
from app.infrastructure.database.models.request_status_history import (
    RequestStatusHistoryModel,
)


async def _create_organization(api_client: AsyncClient, name: str, slug: str) -> dict:
    response = await api_client.post("/organizations", json={"name": name, "slug": slug})
    assert response.status_code == 201
    return response.json()


async def _create_user(
    api_client: AsyncClient,
    email: str,
    full_name: str,
    password: str = "StrongPass123!",
) -> dict:
    response = await api_client.post(
        "/users",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert response.status_code == 201
    return response.json()


async def _login(
    api_client: AsyncClient,
    email: str,
    password: str = "StrongPass123!",
) -> dict:
    response = await api_client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def _membership_headers(access_token: str, membership_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Membership-Id": membership_id,
    }


async def _create_membership(
    api_client: AsyncClient,
    organization_id: str,
    user_id: str,
    role: str = "ADMIN",
) -> dict:
    response = await api_client.post(
        f"/organizations/{organization_id}/memberships",
        json={"user_id": user_id, "role": role},
    )
    assert response.status_code == 201
    return response.json()


async def _create_request(
    api_client: AsyncClient,
    membership_id: str,
    access_token: str,
    title: str = "Need industrial filters",
    customer_id: str | None = None,
    extra_payload: dict | None = None,
) -> dict:
    payload = {
        "title": title,
        "description": "Initial request payload",
        "source": RequestSource.EMAIL.value,
    }
    if customer_id is not None:
        payload["customer_id"] = customer_id
    if extra_payload is not None:
        payload.update(extra_payload)

    response = await api_client.post(
        "/requests",
        json=payload,
        headers=_membership_headers(access_token, membership_id),
    )
    assert response.status_code == 201
    return response.json()


async def _create_request_comment(
    api_client: AsyncClient,
    request_id: str,
    membership_id: str,
    access_token: str,
    body: str = "Initial internal comment",
) -> dict:
    response = await api_client.post(
        f"/requests/{request_id}/comments",
        json={"body": body},
        headers=_membership_headers(access_token, membership_id),
    )
    assert response.status_code == 201
    return response.json()


async def _update_request(
    api_client: AsyncClient,
    request_id: str,
    membership_id: str,
    access_token: str,
    payload: dict,
):
    return await api_client.patch(
        f"/requests/{request_id}",
        json=payload,
        headers=_membership_headers(access_token, membership_id),
    )


async def _create_customer(
    session_factory: async_sessionmaker[AsyncSession],
    organization_id: str,
    name: str = "Acme Customer",
) -> dict:
    now = datetime.now(UTC)
    customer = CustomerModel(
        id=uuid4(),
        organization_id=UUID(organization_id),
        name=name,
        created_at=now,
        updated_at=now,
    )
    async with session_factory() as session:
        session.add(customer)
        await session.commit()

    return {
        "id": str(customer.id),
        "organization_id": organization_id,
        "name": customer.name,
    }


@pytest.mark.anyio
async def test_get_requests_returns_only_active_tenant_requests(api_client: AsyncClient) -> None:
    first_organization = await _create_organization(
        api_client,
        "Tenant Requests One",
        "tenant-requests-one",
    )
    second_organization = await _create_organization(
        api_client,
        "Tenant Requests Two",
        "tenant-requests-two",
    )
    first_user = await _create_user(api_client, "tenant-one@example.com", "Tenant One")
    second_user = await _create_user(api_client, "tenant-two@example.com", "Tenant Two")
    first_membership = await _create_membership(
        api_client,
        first_organization["id"],
        first_user["id"],
    )
    second_membership = await _create_membership(
        api_client,
        second_organization["id"],
        second_user["id"],
    )
    first_auth = await _login(api_client, "tenant-one@example.com")
    second_auth = await _login(api_client, "tenant-two@example.com")

    first_request = await _create_request(
        api_client,
        first_membership["id"],
        first_auth["access_token"],
        title="Tenant one request",
    )
    await _create_request(
        api_client,
        second_membership["id"],
        second_auth["access_token"],
        title="Tenant two request",
    )

    response = await api_client.get(
        "/requests",
        headers=_membership_headers(first_auth["access_token"], first_membership["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == first_request["id"]
    assert payload[0]["organization_id"] == first_organization["id"]
    assert payload[0]["documents_count"] == 0
    assert payload[0]["comments_count"] == 0
    assert payload[0]["customer"] is None
    assert payload[0]["available_status_transitions"] == [
        RequestStatus.UNDER_REVIEW.value
    ]


@pytest.mark.anyio
async def test_get_requests_includes_customer_summary_when_present(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(api_client, "Customer List Org", "customer-list-org")
    user = await _create_user(api_client, "customer-list@example.com", "Customer List")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "customer-list@example.com")
    customer = await _create_customer(session_factory, organization["id"], name="List Customer")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Customer linked request",
        customer_id=customer["id"],
    )

    response = await api_client.get(
        "/requests",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == request_payload["id"]
    assert payload[0]["customer_id"] == customer["id"]
    assert payload[0]["customer"] == {
        "id": customer["id"],
        "name": "List Customer",
    }


@pytest.mark.anyio
async def test_get_requests_supports_title_search(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Search Requests", "search-requests")
    user = await _create_user(api_client, "search-requests@example.com", "Search Requests")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "search-requests@example.com")

    await _create_request(api_client, membership["id"], auth_payload["access_token"], title="Need industrial valves")
    matching_request = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Need stainless pumps",
    )

    response = await api_client.get(
        "/requests?q=stainless",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == matching_request["id"]


@pytest.mark.anyio
async def test_get_requests_includes_comment_counts(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Request Metrics", "request-metrics")
    user = await _create_user(api_client, "request-metrics@example.com", "Request Metrics")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "request-metrics@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )
    await _create_request_comment(
        api_client,
        request_payload["id"],
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.get(
        "/requests",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == request_payload["id"]
    assert payload[0]["comments_count"] == 1


@pytest.mark.anyio
async def test_get_requests_supports_status_filter(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Status Filter Org", "status-filter-org")
    user = await _create_user(api_client, "status-filter@example.com", "Status Filter")
    membership = await _create_membership(api_client, organization["id"], user["id"], role="OWNER")
    auth_payload = await _login(api_client, "status-filter@example.com")

    target_request = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Status filter request",
    )
    transition_response = await api_client.post(
        f"/requests/{target_request['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    assert transition_response.status_code == 200

    response = await api_client.get(
        f"/requests?status={RequestStatus.UNDER_REVIEW.value}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [target_request["id"]]


@pytest.mark.anyio
async def test_get_requests_supports_customer_id_filter(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(api_client, "Customer Filter Org", "customer-filter-org")
    user = await _create_user(api_client, "customer-filter@example.com", "Customer Filter")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "customer-filter@example.com")
    target_customer = await _create_customer(
        session_factory,
        organization["id"],
        name="Target Customer",
    )
    other_customer = await _create_customer(
        session_factory,
        organization["id"],
        name="Other Customer",
    )
    target_request = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Target customer request",
        customer_id=target_customer["id"],
    )
    await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Other customer request",
        customer_id=other_customer["id"],
    )

    response = await api_client.get(
        f"/requests?customer_id={target_customer['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [target_request["id"]]
    assert payload[0]["customer"] == {
        "id": target_customer["id"],
        "name": "Target Customer",
    }


@pytest.mark.anyio
async def test_get_requests_supports_combined_status_and_customer_filters(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(api_client, "Combined Filter Org", "combined-filter-org")
    user = await _create_user(api_client, "combined-filter@example.com", "Combined Filter")
    membership = await _create_membership(api_client, organization["id"], user["id"], role="OWNER")
    auth_payload = await _login(api_client, "combined-filter@example.com")
    target_customer = await _create_customer(
        session_factory,
        organization["id"],
        name="Combined Customer",
    )
    other_customer = await _create_customer(
        session_factory,
        organization["id"],
        name="Other Combined Customer",
    )
    matching_request = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Matching combined request",
        customer_id=target_customer["id"],
    )
    wrong_status_request = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Wrong status combined request",
        customer_id=target_customer["id"],
    )
    await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Wrong customer combined request",
        customer_id=other_customer["id"],
    )

    matching_transition = await api_client.post(
        f"/requests/{matching_request['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    assert matching_transition.status_code == 200

    response = await api_client.get(
        f"/requests?status={RequestStatus.UNDER_REVIEW.value}&customer_id={target_customer['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [matching_request["id"]]
    assert payload[0]["customer"] == {
        "id": target_customer["id"],
        "name": "Combined Customer",
    }


@pytest.mark.anyio
async def test_get_requests_customer_id_filter_does_not_expose_foreign_tenant_requests(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_organization = await _create_organization(
        api_client,
        "Customer Scope One",
        "customer-scope-one",
    )
    second_organization = await _create_organization(
        api_client,
        "Customer Scope Two",
        "customer-scope-two",
    )
    first_user = await _create_user(api_client, "customer-scope-one@example.com", "Customer Scope One")
    second_user = await _create_user(api_client, "customer-scope-two@example.com", "Customer Scope Two")
    first_membership = await _create_membership(api_client, first_organization["id"], first_user["id"])
    second_membership = await _create_membership(api_client, second_organization["id"], second_user["id"])
    first_auth = await _login(api_client, "customer-scope-one@example.com")
    second_auth = await _login(api_client, "customer-scope-two@example.com")
    foreign_customer = await _create_customer(
        session_factory,
        second_organization["id"],
        name="Foreign Filter Customer",
    )
    await _create_request(
        api_client,
        second_membership["id"],
        second_auth["access_token"],
        title="Foreign customer request",
        customer_id=foreign_customer["id"],
    )

    response = await api_client.get(
        f"/requests?customer_id={foreign_customer['id']}",
        headers=_membership_headers(first_auth["access_token"], first_membership["id"]),
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_requests_supports_assigned_membership_filter(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Assignee Filter Org", "assignee-filter-org")
    owner = await _create_user(api_client, "assignee-owner@example.com", "Assignee Owner")
    assignee = await _create_user(api_client, "assignee-user@example.com", "Assignee User")
    owner_membership = await _create_membership(api_client, organization["id"], owner["id"], role="OWNER")
    assignee_membership = await _create_membership(api_client, organization["id"], assignee["id"], role="MEMBER")
    auth_payload = await _login(api_client, "assignee-owner@example.com")
    request_payload = await _create_request(api_client, owner_membership["id"], auth_payload["access_token"])

    assign_response = await api_client.patch(
        f"/requests/{request_payload['id']}/assign",
        json={"assigned_membership_id": assignee_membership["id"]},
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )
    assert assign_response.status_code == 200

    response = await api_client.get(
        f"/requests?assigned_membership_id={assignee_membership['id']}",
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [request_payload["id"]]


@pytest.mark.anyio
async def test_get_requests_supports_source_filter(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Source Filter Org", "source-filter-org")
    user = await _create_user(api_client, "source-filter@example.com", "Source Filter")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "source-filter@example.com")

    await _create_request(api_client, membership["id"], auth_payload["access_token"], title="Email request")
    response_manual = await api_client.post(
        "/requests",
        json={
            "title": "Manual request",
            "description": "Created manually",
            "source": RequestSource.MANUAL.value,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    assert response_manual.status_code == 201

    response = await api_client.get(
        f"/requests?source={RequestSource.MANUAL.value}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert [item["source"] for item in response.json()] == [RequestSource.MANUAL.value]


@pytest.mark.anyio
async def test_post_requests_creates_request(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Acme Requests", "acme-requests")
    user = await _create_user(api_client, "requester@example.com", "Requester Example")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "requester@example.com")

    response = await api_client.post(
        "/requests",
        json={
            "title": "Need stainless steel pumps",
            "description": "For new production line",
            "source": RequestSource.EMAIL.value,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    payload = response.json()

    assert response.status_code == 201
    assert payload["organization_id"] == organization["id"]
    assert payload["created_by_membership_id"] == membership["id"]
    assert payload["title"] == "Need stainless steel pumps"
    assert payload["description"] == "For new production line"
    assert payload["source"] == RequestSource.EMAIL.value
    assert payload["status"] == RequestStatus.NEW.value


@pytest.mark.anyio
async def test_post_requests_creates_request_with_customer_from_same_organization(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(
        api_client,
        "Customer Request Org",
        "customer-request-org",
    )
    user = await _create_user(
        api_client,
        "customer-requester@example.com",
        "Customer Requester",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "customer-requester@example.com")
    customer = await _create_customer(session_factory, organization["id"])

    response = await api_client.post(
        "/requests",
        json={
            "title": "Customer scoped request",
            "description": "Must link only within tenant",
            "source": RequestSource.EMAIL.value,
            "customer_id": customer["id"],
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    payload = response.json()

    assert response.status_code == 201
    assert payload["organization_id"] == organization["id"]
    assert payload["customer_id"] == customer["id"]

    async with session_factory() as session:
        stored_request = await session.scalar(
            select(RequestModel).where(RequestModel.id == UUID(payload["id"]))
        )

    assert stored_request is not None
    assert str(stored_request.organization_id) == organization["id"]
    assert str(stored_request.customer_id) == customer["id"]


@pytest.mark.anyio
async def test_post_requests_rejects_missing_customer(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client,
        "Missing Customer Org",
        "missing-customer-org",
    )
    user = await _create_user(
        api_client,
        "missing-customer@example.com",
        "Missing Customer",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "missing-customer@example.com")

    response = await api_client.post(
        "/requests",
        json={
            "title": "Missing customer link",
            "description": "Should fail with not found",
            "source": RequestSource.API.value,
            "customer_id": str(uuid4()),
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_requests_rejects_customer_from_other_organization(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(
        api_client,
        "Local Customer Org",
        "local-customer-org",
    )
    foreign_organization = await _create_organization(
        api_client,
        "Foreign Customer Org",
        "foreign-customer-org",
    )
    user = await _create_user(api_client, "local-customer@example.com", "Local Customer")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "local-customer@example.com")
    foreign_customer = await _create_customer(
        session_factory,
        foreign_organization["id"],
        name="Foreign Customer",
    )

    response = await api_client.post(
        "/requests",
        json={
            "title": "Cross tenant customer link",
            "description": "Should not leak tenant existence",
            "source": RequestSource.WEB_FORM.value,
            "customer_id": foreign_customer["id"],
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_requests_ignores_payload_organization_id(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(
        api_client,
        "Payload Org Source",
        "payload-org-source",
    )
    other_organization = await _create_organization(
        api_client,
        "Payload Org Foreign",
        "payload-org-foreign",
    )
    user = await _create_user(api_client, "payload-org@example.com", "Payload Org")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "payload-org@example.com")
    customer = await _create_customer(session_factory, organization["id"], name="Scoped Customer")

    response = await api_client.post(
        "/requests",
        json={
            "title": "Payload organization ignored",
            "description": "Context organization must win",
            "source": RequestSource.MANUAL.value,
            "customer_id": customer["id"],
            "organization_id": other_organization["id"],
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    payload = response.json()

    assert response.status_code == 201
    assert payload["organization_id"] == organization["id"]
    assert payload["customer_id"] == customer["id"]

    async with session_factory() as session:
        stored_request = await session.scalar(
            select(RequestModel).where(RequestModel.id == UUID(payload["id"]))
        )

    assert stored_request is not None
    assert str(stored_request.organization_id) == organization["id"]


@pytest.mark.anyio
async def test_post_requests_allows_member_role(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Member Requests", "member-requests")
    user = await _create_user(api_client, "member-requester@example.com", "Member Requester")
    membership = await _create_membership(
        api_client,
        organization["id"],
        user["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "member-requester@example.com")

    response = await api_client.post(
        "/requests",
        json={
            "title": "Need industrial valves",
            "description": "Requested by member",
            "source": RequestSource.WEB_FORM.value,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 201
    assert response.json()["created_by_membership_id"] == membership["id"]
    assert response.json()["status"] == RequestStatus.NEW.value


@pytest.mark.anyio
async def test_get_request_by_id_returns_existing_request(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Nova Requests", "nova-requests")
    user = await _create_user(api_client, "nova-requester@example.com", "Nova Requester")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "nova-requester@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Need conveyor belt",
    )

    response = await api_client.get(
        f"/requests/{request_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == request_payload["id"]
    assert response.json()["status"] == RequestStatus.NEW.value
    assert response.json()["customer"] is None


@pytest.mark.anyio
async def test_get_request_by_id_includes_customer_summary(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(api_client, "Request Customer Org", "request-customer-org")
    user = await _create_user(api_client, "request-customer@example.com", "Request Customer")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "request-customer@example.com")
    customer = await _create_customer(
        session_factory,
        organization["id"],
        name="Visible Customer",
    )
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Need customer context",
        customer_id=customer["id"],
    )

    response = await api_client.get(
        f"/requests/{request_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == request_payload["id"]
    assert response.json()["customer_id"] == customer["id"]
    assert response.json()["customer"] == {
        "id": customer["id"],
        "name": "Visible Customer",
    }


@pytest.mark.anyio
async def test_patch_request_updates_editable_fields_within_same_tenant(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(api_client, "Update Requests", "update-requests")
    user = await _create_user(api_client, "update-requester@example.com", "Update Requester")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "update-requester@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Original request title",
    )
    customer = await _create_customer(session_factory, organization["id"], name="Updated Customer")

    response = await _update_request(
        api_client,
        request_payload["id"],
        membership["id"],
        auth_payload["access_token"],
        {
            "title": "Updated request title",
            "description": "Updated request description",
            "customer_id": customer["id"],
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == request_payload["id"]
    assert payload["organization_id"] == organization["id"]
    assert payload["title"] == "Updated request title"
    assert payload["description"] == "Updated request description"
    assert payload["customer_id"] == customer["id"]

    async with session_factory() as session:
        stored_request = await session.scalar(
            select(RequestModel).where(RequestModel.id == UUID(request_payload["id"]))
        )

    assert stored_request is not None
    assert stored_request.title == "Updated request title"
    assert stored_request.description == "Updated request description"
    assert str(stored_request.customer_id) == customer["id"]

    activities_response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert activities_response.status_code == 200
    assert any(
        activity["type"] == "REQUEST_UPDATED"
        and activity["membership_id"] == membership["id"]
        and activity["payload"]["request_id"] == request_payload["id"]
        and activity["payload"]["actor_user_id"] == user["id"]
        and activity["payload"]["updated_fields"]
        == ["title", "description", "customer_id"]
        for activity in activities_response.json()
    )


@pytest.mark.anyio
async def test_patch_request_returns_not_found_for_missing_request(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Missing Update", "missing-update")
    user = await _create_user(api_client, "missing-update@example.com", "Missing Update")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "missing-update@example.com")

    response = await _update_request(
        api_client,
        str(uuid4()),
        membership["id"],
        auth_payload["access_token"],
        {"title": "Updated title"},
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_patch_request_returns_not_found_for_foreign_tenant(
    api_client: AsyncClient,
) -> None:
    owner_organization = await _create_organization(api_client, "Owner Update", "owner-update")
    foreign_organization = await _create_organization(
        api_client,
        "Foreign Update",
        "foreign-update",
    )
    owner_user = await _create_user(api_client, "owner-update@example.com", "Owner Update")
    foreign_user = await _create_user(
        api_client,
        "foreign-update@example.com",
        "Foreign Update",
    )
    owner_membership = await _create_membership(
        api_client,
        owner_organization["id"],
        owner_user["id"],
    )
    foreign_membership = await _create_membership(
        api_client,
        foreign_organization["id"],
        foreign_user["id"],
    )
    owner_auth = await _login(api_client, "owner-update@example.com")
    foreign_auth = await _login(api_client, "foreign-update@example.com")
    request_payload = await _create_request(
        api_client,
        owner_membership["id"],
        owner_auth["access_token"],
    )

    response = await _update_request(
        api_client,
        request_payload["id"],
        foreign_membership["id"],
        foreign_auth["access_token"],
        {"title": "Foreign update attempt"},
    )

    assert response.status_code == 404

    activities_response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(owner_auth["access_token"], owner_membership["id"]),
    )

    assert activities_response.status_code == 200
    assert [activity["type"] for activity in activities_response.json()] == [
        "REQUEST_CREATED"
    ]


@pytest.mark.anyio
async def test_patch_request_rejects_customer_from_other_organization(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(api_client, "Scoped Update", "scoped-update")
    foreign_organization = await _create_organization(
        api_client,
        "Scoped Update Foreign",
        "scoped-update-foreign",
    )
    user = await _create_user(api_client, "scoped-update@example.com", "Scoped Update")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "scoped-update@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )
    foreign_customer = await _create_customer(
        session_factory,
        foreign_organization["id"],
        name="Foreign Customer",
    )

    response = await _update_request(
        api_client,
        request_payload["id"],
        membership["id"],
        auth_payload["access_token"],
        {"customer_id": foreign_customer["id"]},
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_comments_creates_comment_and_activity(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Comment Org", "comment-org")
    user = await _create_user(api_client, "commenter@example.com", "Commenter")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "commenter@example.com")
    request_payload = await _create_request(api_client, membership["id"], auth_payload["access_token"])

    response = await api_client.post(
        f"/requests/{request_payload['id']}/comments",
        json={"body": "Need to validate lead times with procurement."},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["request_id"] == request_payload["id"]
    assert payload["membership_id"] == membership["id"]
    assert payload["body"] == "Need to validate lead times with procurement."

    comments_response = await api_client.get(
        f"/requests/{request_payload['id']}/comments",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    assert comments_response.status_code == 200
    assert comments_response.json()[0]["id"] == payload["id"]

    activities_response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    assert activities_response.status_code == 200
    assert any(
        activity["type"] == "REQUEST_COMMENT_ADDED"
        and activity["payload"]["comment_id"] == payload["id"]
        for activity in activities_response.json()
    )


@pytest.mark.anyio
async def test_request_comments_are_tenant_scoped(api_client: AsyncClient) -> None:
    first_organization = await _create_organization(api_client, "Comment Tenant One", "comment-tenant-one")
    second_organization = await _create_organization(api_client, "Comment Tenant Two", "comment-tenant-two")
    first_user = await _create_user(api_client, "comment-tenant-one@example.com", "Comment Tenant One")
    second_user = await _create_user(api_client, "comment-tenant-two@example.com", "Comment Tenant Two")
    first_membership = await _create_membership(api_client, first_organization["id"], first_user["id"])
    second_membership = await _create_membership(api_client, second_organization["id"], second_user["id"])
    first_auth = await _login(api_client, "comment-tenant-one@example.com")
    second_auth = await _login(api_client, "comment-tenant-two@example.com")
    request_payload = await _create_request(api_client, first_membership["id"], first_auth["access_token"])

    response = await api_client.post(
        f"/requests/{request_payload['id']}/comments",
        json={"body": "Attempting cross-tenant comment"},
        headers=_membership_headers(second_auth["access_token"], second_membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_request_comments_require_authentication(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Comment Auth Org", "comment-auth-org")
    user = await _create_user(api_client, "comment-auth@example.com", "Comment Auth")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "comment-auth@example.com")
    request_payload = await _create_request(api_client, membership["id"], auth_payload["access_token"])
    api_client.cookies.clear()

    response = await api_client.post(
        f"/requests/{request_payload['id']}/comments",
        json={"body": "Unauthenticated comment attempt"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_patch_assign_request_updates_assigned_membership(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Assign Org", "assign-org")
    owner = await _create_user(api_client, "assign-owner@example.com", "Assign Owner")
    assignee = await _create_user(api_client, "assign-user@example.com", "Assign User")
    owner_membership = await _create_membership(
        api_client,
        organization["id"],
        owner["id"],
        role="OWNER",
    )
    assignee_membership = await _create_membership(
        api_client,
        organization["id"],
        assignee["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "assign-owner@example.com")
    request_payload = await _create_request(api_client, owner_membership["id"], auth_payload["access_token"])

    response = await api_client.patch(
        f"/requests/{request_payload['id']}/assign",
        json={"assigned_membership_id": assignee_membership["id"]},
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["assigned_membership_id"] == assignee_membership["id"]

    activities_response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )
    assert activities_response.status_code == 200
    assert any(
        activity["type"] == "REQUEST_ASSIGNED"
        and activity["payload"]["assigned_membership_id"] == assignee_membership["id"]
        for activity in activities_response.json()
    )


@pytest.mark.anyio
async def test_patch_assign_request_is_tenant_scoped(api_client: AsyncClient) -> None:
    first_organization = await _create_organization(api_client, "Assign Tenant One", "assign-tenant-one")
    second_organization = await _create_organization(api_client, "Assign Tenant Two", "assign-tenant-two")
    first_user = await _create_user(api_client, "assign-tenant-one@example.com", "Assign Tenant One")
    second_user = await _create_user(api_client, "assign-tenant-two@example.com", "Assign Tenant Two")
    first_membership = await _create_membership(api_client, first_organization["id"], first_user["id"], role="OWNER")
    second_membership = await _create_membership(api_client, second_organization["id"], second_user["id"], role="OWNER")
    first_auth = await _login(api_client, "assign-tenant-one@example.com")
    second_auth = await _login(api_client, "assign-tenant-two@example.com")
    request_payload = await _create_request(api_client, first_membership["id"], first_auth["access_token"])

    response = await api_client.patch(
        f"/requests/{request_payload['id']}/assign",
        json={"assigned_membership_id": second_membership["id"]},
        headers=_membership_headers(first_auth["access_token"], first_membership["id"]),
    )

    assert response.status_code == 409

    forbidden_response = await api_client.patch(
        f"/requests/{request_payload['id']}/assign",
        json={"assigned_membership_id": first_membership["id"]},
        headers=_membership_headers(second_auth["access_token"], second_membership["id"]),
    )

    assert forbidden_response.status_code == 404


@pytest.mark.anyio
async def test_patch_assign_request_requires_authentication(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Assign Auth Org", "assign-auth-org")
    user = await _create_user(api_client, "assign-auth@example.com", "Assign Auth")
    membership = await _create_membership(api_client, organization["id"], user["id"], role="OWNER")
    auth_payload = await _login(api_client, "assign-auth@example.com")
    request_payload = await _create_request(api_client, membership["id"], auth_payload["access_token"])
    api_client.cookies.clear()

    response = await api_client.patch(
        f"/requests/{request_payload['id']}/assign",
        json={"assigned_membership_id": membership["id"]},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_post_requests_returns_401_without_authentication(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        "/requests",
        json={
            "title": "Missing auth request",
            "description": None,
            "source": RequestSource.API.value,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


@pytest.mark.anyio
async def test_post_requests_returns_401_for_membership_from_other_user(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Alpha Requests", "alpha-requests")
    owner_user = await _create_user(api_client, "owner@example.com", "Owner User")
    intruder_user = await _create_user(api_client, "intruder@example.com", "Intruder User")
    foreign_membership = await _create_membership(
        api_client,
        organization["id"],
        owner_user["id"],
    )
    intruder_auth = await _login(api_client, "intruder@example.com")

    response = await api_client.post(
        "/requests",
        json={
            "title": "Foreign membership request",
            "description": None,
            "source": RequestSource.EMAIL.value,
        },
        headers=_membership_headers(intruder_auth["access_token"], foreign_membership["id"]),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Membership context is invalid."


@pytest.mark.anyio
async def test_get_requests_rejects_spoofed_membership_context(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Spoof Requests", "spoof-requests")
    owner = await _create_user(api_client, "spoof-requests-owner@example.com", "Spoof Requests Owner")
    intruder = await _create_user(api_client, "spoof-requests-intruder@example.com", "Spoof Requests Intruder")
    owner_membership = await _create_membership(
        api_client,
        organization["id"],
        owner["id"],
        role="OWNER",
    )
    intruder_membership = await _create_membership(
        api_client,
        organization["id"],
        intruder["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "spoof-requests-owner@example.com")
    await _create_request(api_client, owner_membership["id"], auth_payload["access_token"])

    response = await api_client.get(
        "/requests",
        headers=_membership_headers(auth_payload["access_token"], intruder_membership["id"]),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Membership context is invalid."


@pytest.mark.anyio
async def test_get_request_by_id_returns_not_found(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Missing Requests", "missing-requests")
    user = await _create_user(api_client, "missing-requests@example.com", "Missing Requests")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "missing-requests@example.com")

    response = await api_client.get(
        f"/requests/{uuid4()}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_request_by_id_returns_not_found_for_foreign_tenant(
    api_client: AsyncClient,
) -> None:
    owner_organization = await _create_organization(
        api_client,
        "Owner Requests",
        "owner-requests",
    )
    foreign_organization = await _create_organization(
        api_client,
        "Foreign Requests",
        "foreign-requests",
    )
    owner_user = await _create_user(api_client, "owner-requests@example.com", "Owner Requests")
    foreign_user = await _create_user(
        api_client,
        "foreign-requests@example.com",
        "Foreign Requests",
    )
    owner_membership = await _create_membership(
        api_client,
        owner_organization["id"],
        owner_user["id"],
    )
    foreign_membership = await _create_membership(
        api_client,
        foreign_organization["id"],
        foreign_user["id"],
    )
    owner_auth = await _login(api_client, "owner-requests@example.com")
    foreign_auth = await _login(api_client, "foreign-requests@example.com")
    request_payload = await _create_request(
        api_client,
        owner_membership["id"],
        owner_auth["access_token"],
    )

    response = await api_client.get(
        f"/requests/{request_payload['id']}",
        headers=_membership_headers(foreign_auth["access_token"], foreign_membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_status_transitions_updates_request_status(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Transition Org", "transition-org")
    user = await _create_user(api_client, "transition@example.com", "Transition User")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "transition@example.com")
    request_payload = await _create_request(
        api_client=api_client,
        membership_id=membership["id"],
        access_token=auth_payload["access_token"],
        title="Need stainless steel pumps",
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == request_payload["id"]
    assert response.json()["status"] == RequestStatus.UNDER_REVIEW.value


@pytest.mark.anyio
async def test_post_request_status_transitions_returns_conflict_for_invalid_transition(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client, "Invalid Transition Org", "invalid-transition-org"
    )
    user = await _create_user(api_client, "invalid-transition@example.com", "Invalid Transition")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "invalid-transition@example.com")
    request_payload = await _create_request(
        api_client=api_client,
        membership_id=membership["id"],
        access_token=auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.WON.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot transition request from 'NEW' to 'WON'."


@pytest.mark.anyio
async def test_post_request_status_transitions_allows_member_role(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Member Transition", "member-transition")
    user = await _create_user(api_client, "member-transition@example.com", "Member Transition")
    membership = await _create_membership(
        api_client,
        organization["id"],
        user["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "member-transition@example.com")
    request_payload = await _create_request(
        api_client=api_client,
        membership_id=membership["id"],
        access_token=auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == RequestStatus.UNDER_REVIEW.value


@pytest.mark.anyio
async def test_post_requests_allows_member_role_without_legacy_viewer(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Member Requests", "member-requests")
    user = await _create_user(api_client, "member-role@example.com", "Member Role User")
    membership = await _create_membership(
        api_client,
        organization["id"],
        user["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "member-role@example.com")

    response = await api_client.post(
        "/requests",
        json={
            "title": "Member can create",
            "description": "Allowed mutation",
            "source": RequestSource.MANUAL.value,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Member can create"


@pytest.mark.anyio
async def test_post_request_status_transitions_returns_not_found_for_missing_request(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client, "Missing Request Transition", "missing-request-transition"
    )
    user = await _create_user(api_client, "missing-request@example.com", "Missing Request")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "missing-request@example.com")

    response = await api_client.post(
        f"/requests/{uuid4()}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_status_transitions_returns_403_for_invalid_membership_context(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client, "Missing Membership Transition", "missing-membership-transition"
    )
    user = await _create_user(
        api_client, "missing-membership@example.com", "Missing Membership"
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "missing-membership@example.com")
    request_payload = await _create_request(
        api_client=api_client,
        membership_id=membership["id"],
        access_token=auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], str(uuid4())),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Membership context is invalid."


@pytest.mark.anyio
async def test_post_request_status_transitions_returns_not_found_for_request_from_other_organization(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client, "Alpha Transition Org", "alpha-transition-org"
    )
    other_organization = await _create_organization(
        api_client, "Beta Transition Org", "beta-transition-org"
    )
    user = await _create_user(api_client, "cross-transition@example.com", "Cross Transition")
    request_membership = await _create_membership(api_client, organization["id"], user["id"])
    other_membership = await _create_membership(api_client, other_organization["id"], user["id"])
    auth_payload = await _login(api_client, "cross-transition@example.com")
    request_payload = await _create_request(
        api_client=api_client,
        membership_id=request_membership["id"],
        access_token=auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], other_membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_status_transitions_creates_status_changed_activity(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client, "Timeline Transition Org", "timeline-transition-org"
    )
    user = await _create_user(api_client, "timeline-transition@example.com", "Timeline Transition")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "timeline-transition@example.com")
    request_payload = await _create_request(
        api_client=api_client,
        membership_id=membership["id"],
        access_token=auth_payload["access_token"],
        title="Need stateful request",
    )

    transition_response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    activities_response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert transition_response.status_code == 200
    assert activities_response.status_code == 200
    activities = activities_response.json()
    assert len(activities) == 2
    assert activities[1]["type"] == "STATUS_CHANGED"
    assert activities[1]["membership_id"] == membership["id"]
    assert activities[1]["payload"]["old_status"] == RequestStatus.NEW.value
    assert activities[1]["payload"]["new_status"] == RequestStatus.UNDER_REVIEW.value


@pytest.mark.anyio
async def test_post_request_status_transitions_persists_status_history(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(
        api_client, "History Transition Org", "history-transition-org"
    )
    user = await _create_user(api_client, "history-transition@example.com", "History Transition")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "history-transition@example.com")
    request_payload = await _create_request(
        api_client=api_client,
        membership_id=membership["id"],
        access_token=auth_payload["access_token"],
        title="Need tracked request",
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200

    async with session_factory() as session:
        history_entries = (
            await session.scalars(
                select(RequestStatusHistoryModel)
                .where(RequestStatusHistoryModel.request_id == UUID(request_payload["id"]))
                .order_by(RequestStatusHistoryModel.changed_at.asc())
            )
        ).all()

    assert len(history_entries) == 2
    assert str(history_entries[0].request_id) == request_payload["id"]
    assert str(history_entries[0].organization_id) == organization["id"]
    assert history_entries[0].previous_status is None
    assert history_entries[0].new_status == RequestStatus.NEW
    assert str(history_entries[0].changed_by) == membership["id"]
    assert str(history_entries[0].changed_by_user_id) == user["id"]
    assert str(history_entries[1].request_id) == request_payload["id"]
    assert str(history_entries[1].organization_id) == organization["id"]
    assert history_entries[1].previous_status == RequestStatus.NEW
    assert history_entries[1].new_status == RequestStatus.UNDER_REVIEW
    assert str(history_entries[1].changed_by) == membership["id"]
    assert str(history_entries[1].changed_by_user_id) == user["id"]
