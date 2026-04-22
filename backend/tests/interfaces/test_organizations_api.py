from uuid import UUID

import pytest
from httpx import AsyncClient


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


async def _create_membership(
    api_client: AsyncClient,
    organization_id: str,
    user_id: str,
    role: str = "OWNER",
) -> dict:
    response = await api_client.post(
        f"/organizations/{organization_id}/memberships",
        json={"user_id": user_id, "role": role},
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


@pytest.mark.anyio
async def test_post_organizations_creates_organization(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/organizations",
        json={"name": "Acme Manufacturing", "slug": "acme-manufacturing"},
    )

    payload = response.json()

    assert response.status_code == 201
    assert payload["name"] == "Acme Manufacturing"
    assert payload["slug"] == "acme-manufacturing"
    assert payload["is_active"] is True
    assert UUID(payload["id"])


@pytest.mark.anyio
async def test_get_organization_by_id_returns_existing_organization(api_client: AsyncClient) -> None:
    create_response = await api_client.post(
        "/organizations",
        json={"name": "Nova Systems", "slug": "nova-systems"},
    )
    organization_id = create_response.json()["id"]
    user = await _create_user(api_client, "nova-org@example.com", "Nova Org")
    membership = await _create_membership(api_client, organization_id, user["id"], role="OWNER")
    auth_payload = await _login(api_client, "nova-org@example.com")

    response = await api_client.get(
        f"/organizations/{organization_id}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == organization_id
    assert response.json()["slug"] == "nova-systems"


@pytest.mark.anyio
async def test_post_organizations_returns_conflict_for_duplicate_slug(
    api_client: AsyncClient,
) -> None:
    first_response = await api_client.post(
        "/organizations",
        json={"name": "Helix", "slug": "helix"},
    )

    second_response = await api_client.post(
        "/organizations",
        json={"name": "Helix Duplicate", "slug": "helix"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Organization slug 'helix' already exists."


@pytest.mark.anyio
async def test_get_organization_by_id_returns_not_found(api_client: AsyncClient) -> None:
    create_response = await api_client.post(
        "/organizations",
        json={"name": "Scoped Systems", "slug": "scoped-systems"},
    )
    user = await _create_user(api_client, "scoped-org@example.com", "Scoped Org")
    membership = await _create_membership(
        api_client,
        create_response.json()["id"],
        user["id"],
        role="OWNER",
    )
    auth_payload = await _login(api_client, "scoped-org@example.com")
    response = await api_client.get(
        "/organizations/00000000-0000-0000-0000-000000000001",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_organization_by_id_rejects_spoofed_membership_context(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Spoof Org", "spoof-org")
    owner = await _create_user(api_client, "spoof-owner@example.com", "Spoof Owner")
    intruder = await _create_user(api_client, "spoof-intruder@example.com", "Spoof Intruder")
    await _create_membership(api_client, organization["id"], owner["id"], role="OWNER")
    intruder_membership = await _create_membership(
        api_client,
        organization["id"],
        intruder["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "spoof-owner@example.com")

    response = await api_client.get(
        f"/organizations/{organization['id']}",
        headers=_membership_headers(auth_payload["access_token"], intruder_membership["id"]),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Membership context is invalid."
