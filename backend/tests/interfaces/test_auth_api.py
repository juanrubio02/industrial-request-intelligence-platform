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
    user = await _create_user(api_client)

    response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == user["id"]
    assert response.json()["user"]["email"] == user["email"]
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert "iri_session=" in response.headers.get("set-cookie", "")


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
async def test_get_auth_me_returns_current_user_with_cookie_session(
    api_client: AsyncClient,
) -> None:
    user = await _create_user(api_client)
    login_response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )

    assert login_response.status_code == 200

    response = await api_client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == user["id"]
    assert response.json()["email"] == user["email"]
    assert response.json()["active_organization"] is None
    assert response.json()["active_membership"] is None


@pytest.mark.anyio
async def test_get_auth_me_returns_active_membership_and_organization_context(
    api_client: AsyncClient,
) -> None:
    user = await _create_user(api_client)
    organization = await _create_organization(api_client, "Acme Industrial", "acme-industrial")
    membership = await _create_membership(
        api_client,
        organization["id"],
        user["id"],
        role="OWNER",
    )
    await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )

    response = await api_client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == user["id"]
    assert response.json()["active_organization"] == {
        "id": organization["id"],
        "name": "Acme Industrial",
        "slug": "acme-industrial",
    }
    assert response.json()["active_membership"] == {
        "id": membership["id"],
        "role": "OWNER",
        "status": "ACTIVE",
    }


@pytest.mark.anyio
async def test_get_auth_me_returns_401_without_authentication(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


@pytest.mark.anyio
async def test_post_auth_logout_clears_cookie_session(
    api_client: AsyncClient,
) -> None:
    await _create_user(api_client)
    login_response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )

    assert login_response.status_code == 200

    logout_response = await api_client.post("/auth/logout")

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out successfully."
    set_cookie_header = logout_response.headers.get("set-cookie", "")
    assert "iri_session=\"\"" in set_cookie_header
    assert "iri_refresh=\"\"" in set_cookie_header

    me_response = await api_client.get("/auth/me")

    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Invalid or expired access token."


@pytest.mark.anyio
async def test_post_auth_refresh_rotates_refresh_cookie(
    api_client: AsyncClient,
) -> None:
    await _create_user(api_client)
    login_response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )
    original_refresh_token = api_client.cookies.get("iri_refresh")

    refresh_response = await api_client.post("/auth/refresh")

    assert refresh_response.status_code == 200
    assert api_client.cookies.get("iri_refresh") != original_refresh_token
    assert "iri_refresh=" in refresh_response.headers.get("set-cookie", "")


@pytest.mark.anyio
async def test_post_auth_refresh_rejects_replayed_refresh_token_and_revokes_rotated_session(
    api_client: AsyncClient,
) -> None:
    await _create_user(api_client)
    login_response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )
    original_refresh_token = api_client.cookies.get("iri_refresh")

    refresh_response = await api_client.post("/auth/refresh")

    assert refresh_response.status_code == 200
    rotated_refresh_token = api_client.cookies.get("iri_refresh")

    api_client.cookies.set("iri_refresh", original_refresh_token)
    replay_response = await api_client.post("/auth/refresh")

    assert replay_response.status_code == 401
    assert replay_response.json()["detail"] == "Invalid or expired refresh token."

    api_client.cookies.set("iri_refresh", rotated_refresh_token)
    revoked_rotated_response = await api_client.post("/auth/refresh")

    assert revoked_rotated_response.status_code == 401
    assert revoked_rotated_response.json()["detail"] == "Invalid or expired refresh token."


@pytest.mark.anyio
async def test_post_auth_logout_revokes_refresh_session_server_side(
    api_client: AsyncClient,
) -> None:
    await _create_user(api_client)
    login_response = await api_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )
    original_refresh_token = api_client.cookies.get("iri_refresh")

    logout_response = await api_client.post("/auth/logout")

    assert logout_response.status_code == 200
    api_client.cookies.set("iri_refresh", original_refresh_token)
    refresh_response = await api_client.post("/auth/refresh")

    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Invalid or expired refresh token."


@pytest.mark.anyio
async def test_get_auth_memberships_returns_user_memberships(
    api_client: AsyncClient,
) -> None:
    user = await _create_user(api_client)
    organization = await _create_organization(
        api_client,
        "Industrial Workspace",
        "forgeflow-workspace",
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
    assert response.json()[0]["organization_slug"] == "forgeflow-workspace"
    assert response.json()[0]["role"] == "OWNER"
    assert response.json()[0]["status"] == "ACTIVE"


@pytest.mark.anyio
async def test_get_auth_memberships_returns_401_without_authentication(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/auth/memberships")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."


@pytest.mark.anyio
async def test_get_requests_returns_401_without_authentication(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/requests")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."
