from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


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
) -> dict:
    response = await api_client.post(
        "/requests",
        json={
            "title": title,
            "description": "Initial request payload",
            "source": RequestSource.EMAIL.value,
        },
        headers=_membership_headers(access_token, membership_id),
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_post_requests_creates_automatic_request_created_activity(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Acme Timeline", "acme-timeline")
    user = await _create_user(api_client, "timeline@example.com", "Timeline User")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "timeline@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 1
    assert activities[0]["request_id"] == request_payload["id"]
    assert activities[0]["organization_id"] == organization["id"]
    assert activities[0]["membership_id"] == membership["id"]
    assert activities[0]["type"] == "REQUEST_CREATED"
    assert activities[0]["payload"]["request_id"] == request_payload["id"]
    assert activities[0]["payload"]["status"] == RequestStatus.NEW.value


@pytest.mark.anyio
async def test_get_request_activities_returns_request_activities(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Nova Timeline", "nova-timeline")
    user = await _create_user(api_client, "nova-timeline@example.com", "Nova Timeline")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "nova-timeline@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Need conveyor upgrade",
    )

    response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 1
    assert activities[0]["type"] == "REQUEST_CREATED"
    assert activities[0]["payload"]["title"] == "Need conveyor upgrade"


@pytest.mark.anyio
async def test_get_request_activities_returns_not_found_for_missing_request(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Missing Timeline", "missing-timeline")
    user = await _create_user(api_client, "missing-timeline@example.com", "Missing Timeline")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "missing-timeline@example.com")

    response = await api_client.get(
        f"/requests/{uuid4()}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404
