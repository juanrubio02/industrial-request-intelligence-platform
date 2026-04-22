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
    title: str,
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
async def test_get_pipeline_analytics_returns_current_status_counts_and_rates(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client,
        "Analytics API Org",
        "analytics-api-org",
    )
    user = await _create_user(api_client, "analytics-api@example.com", "Analytics API")
    membership = await _create_membership(api_client, organization["id"], user["id"], role="OWNER")
    auth_payload = await _login(api_client, "analytics-api@example.com")

    won_request = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Won request",
    )
    lost_request = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
        title="Lost request",
    )

    for next_status in [
        RequestStatus.UNDER_REVIEW,
        RequestStatus.QUOTE_PREPARING,
        RequestStatus.QUOTE_SENT,
        RequestStatus.WON,
    ]:
        response = await api_client.post(
            f"/requests/{won_request['id']}/status-transitions",
            json={"new_status": next_status.value},
            headers=_membership_headers(auth_payload["access_token"], membership["id"]),
        )
        assert response.status_code == 200

    for next_status in [
        RequestStatus.UNDER_REVIEW,
        RequestStatus.QUOTE_PREPARING,
        RequestStatus.QUOTE_SENT,
        RequestStatus.LOST,
    ]:
        response = await api_client.post(
            f"/requests/{lost_request['id']}/status-transitions",
            json={"new_status": next_status.value},
            headers=_membership_headers(auth_payload["access_token"], membership["id"]),
        )
        assert response.status_code == 200

    response = await api_client.get(
        "/analytics/pipeline",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_requests"] == 2
    assert payload["conversion_rate"] == pytest.approx(0.5, abs=0.0001)
    assert payload["loss_rate"] == pytest.approx(0.5, abs=0.0001)
    assert payload["requests_by_status"]["WON"] == 1
    assert payload["requests_by_status"]["LOST"] == 1
    assert set(payload["avg_time_per_stage"]) == {
        "NEW",
        "UNDER_REVIEW",
        "QUOTE_PREPARING",
        "QUOTE_SENT",
        "NEGOTIATION",
        "WON",
        "LOST",
    }


@pytest.mark.anyio
async def test_get_pipeline_analytics_requires_membership_context(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client,
        "Analytics Context Org",
        "analytics-context-org",
    )
    user = await _create_user(api_client, "analytics-context@example.com", "Analytics Context")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "analytics-context@example.com")

    response = await api_client.get(
        "/analytics/pipeline",
        headers={"Authorization": f"Bearer {auth_payload['access_token']}"},
    )

    assert membership["id"]  # keep fixture setup explicit
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_pipeline_analytics_is_scoped_to_active_tenant(
    api_client: AsyncClient,
) -> None:
    first_organization = await _create_organization(
        api_client,
        "Analytics Tenant One",
        "analytics-tenant-one",
    )
    second_organization = await _create_organization(
        api_client,
        "Analytics Tenant Two",
        "analytics-tenant-two",
    )
    user = await _create_user(api_client, "analytics-tenant@example.com", "Tenant User")
    first_membership = await _create_membership(
        api_client,
        first_organization["id"],
        user["id"],
        role="OWNER",
    )
    second_membership = await _create_membership(
        api_client,
        second_organization["id"],
        user["id"],
        role="OWNER",
    )
    auth_payload = await _login(api_client, "analytics-tenant@example.com")

    await _create_request(
        api_client,
        first_membership["id"],
        auth_payload["access_token"],
        title="Tenant one request",
    )
    await _create_request(
        api_client,
        second_membership["id"],
        auth_payload["access_token"],
        title="Tenant two request",
    )

    response = await api_client.get(
        "/analytics/pipeline",
        headers=_membership_headers(auth_payload["access_token"], first_membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["total_requests"] == 1
