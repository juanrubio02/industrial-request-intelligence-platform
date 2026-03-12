import pytest
from httpx import AsyncClient


async def _create_user(
    api_client: AsyncClient,
    email: str = "alice@example.com",
    full_name: str = "Alice Example",
    password: str = "StrongPass123!",
) -> dict:
    response = await api_client.post(
        "/users",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert response.status_code == 201
    return response.json()


async def _create_organization(api_client: AsyncClient, name: str, slug: str) -> dict:
    response = await api_client.post("/organizations", json={"name": name, "slug": slug})
    assert response.status_code == 201
    return response.json()


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


@pytest.mark.anyio
async def test_post_auth_login_returns_token_for_valid_credentials(
    api_client: AsyncClient,
) -> None:
    await _create_user(api_client)

    response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


@pytest.mark.anyio
async def test_post_auth_login_returns_401_for_invalid_credentials(
    api_client: AsyncClient,
) -> None:
    await _create_user(api_client)

    response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "WrongPass123!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.anyio
async def test_get_auth_me_returns_current_user_with_valid_token(
    api_client: AsyncClient,
) -> None:
    user = await _create_user(api_client)
    login_response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )

    response = await api_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == user["id"]
    assert response.json()["email"] == user["email"]


@pytest.mark.anyio
async def test_get_auth_me_returns_401_without_authentication(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


@pytest.mark.anyio
async def test_get_auth_memberships_returns_user_memberships(
    api_client: AsyncClient,
) -> None:
    user = await _create_user(api_client)
    organization = await _create_organization(
        api_client,
        "Industrial Workspace",
        "industrial-workspace",
    )
    await _create_membership(api_client, organization["id"], user["id"], role="OWNER")
    login_response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )

    response = await api_client.get(
        "/auth/memberships",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["organization_id"] == organization["id"]
    assert response.json()[0]["organization_name"] == "Industrial Workspace"
    assert response.json()[0]["role"] == "OWNER"
