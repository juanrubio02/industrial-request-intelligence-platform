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
async def test_post_request_status_transitions_applies_valid_transition(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Acme Pipeline", "acme-pipeline")
    user = await _create_user(api_client, "pipeline@example.com", "Pipeline User")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "pipeline@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == RequestStatus.UNDER_REVIEW.value


@pytest.mark.anyio
async def test_post_request_status_transitions_rejects_invalid_transition(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Nova Pipeline", "nova-pipeline")
    user = await _create_user(api_client, "nova-pipeline@example.com", "Nova Pipeline")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "nova-pipeline@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.WON.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot transition request from 'NEW' to 'WON'."


@pytest.mark.anyio
async def test_post_request_status_transitions_returns_not_found_for_missing_request(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Orbit Pipeline", "orbit-pipeline")
    user = await _create_user(api_client, "orbit-pipeline@example.com", "Orbit Pipeline")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "orbit-pipeline@example.com")

    response = await api_client.post(
        f"/requests/{uuid4()}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_status_transitions_returns_403_for_missing_membership_context(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Helix Pipeline", "helix-pipeline")
    user = await _create_user(api_client, "helix-pipeline@example.com", "Helix Pipeline")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "helix-pipeline@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers={"Authorization": f"Bearer {auth_payload['access_token']}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "A valid membership context is required."


@pytest.mark.anyio
async def test_post_request_status_transitions_returns_conflict_for_membership_from_other_organization(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Alpha Pipeline", "alpha-pipeline")
    other_organization = await _create_organization(api_client, "Beta Pipeline", "beta-pipeline")
    user = await _create_user(api_client, "cross-pipeline@example.com", "Cross Pipeline")
    request_membership = await _create_membership(api_client, organization["id"], user["id"])
    actor_membership = await _create_membership(api_client, other_organization["id"], user["id"])
    auth_payload = await _login(api_client, "cross-pipeline@example.com")
    request_payload = await _create_request(
        api_client,
        request_membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/status-transitions",
        json={"new_status": RequestStatus.UNDER_REVIEW.value},
        headers=_membership_headers(auth_payload["access_token"], actor_membership["id"]),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "The provided request does not belong to the provided organization."
    )


@pytest.mark.anyio
async def test_post_request_status_transitions_creates_status_changed_activity(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Sigma Pipeline", "sigma-pipeline")
    user = await _create_user(api_client, "sigma-pipeline@example.com", "Sigma Pipeline")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "sigma-pipeline@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
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
    assert activities[1]["payload"]["old_status"] == RequestStatus.NEW.value
    assert activities[1]["payload"]["new_status"] == RequestStatus.UNDER_REVIEW.value
