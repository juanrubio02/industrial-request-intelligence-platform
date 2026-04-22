import pytest
from httpx import AsyncClient


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


async def _login(api_client: AsyncClient, email: str, password: str = "StrongPass123!") -> dict:
    response = await api_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


def _membership_headers(access_token: str, membership_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Membership-Id": membership_id,
    }


@pytest.mark.anyio
async def test_get_organization_members_returns_only_members_from_active_organization(
    api_client: AsyncClient,
) -> None:
    first_organization = await _create_organization(api_client, "Alpha Org", "alpha-org")
    second_organization = await _create_organization(api_client, "Beta Org", "beta-org")
    owner = await _create_user(api_client, "owner@example.com", "Owner User")
    teammate = await _create_user(api_client, "teammate@example.com", "Teammate User")
    outsider = await _create_user(api_client, "outsider@example.com", "Outsider User")
    owner_membership = await _create_membership(
        api_client,
        first_organization["id"],
        owner["id"],
        role="OWNER",
    )
    await _create_membership(api_client, first_organization["id"], teammate["id"], role="MEMBER")
    await _create_membership(api_client, second_organization["id"], outsider["id"], role="OWNER")
    auth_payload = await _login(api_client, "owner@example.com")

    response = await api_client.get(
        f"/organizations/{first_organization['id']}/memberships",
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 200
    members = response.json()
    assert [member["user_email"] for member in members] == [
        "owner@example.com",
        "teammate@example.com",
    ]
    assert all(member["organization_id"] == first_organization["id"] for member in members)


@pytest.mark.anyio
async def test_patch_organization_member_role_updates_role_in_active_organization(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Role Org", "role-org")
    owner = await _create_user(api_client, "role-owner@example.com", "Role Owner")
    member = await _create_user(api_client, "role-member@example.com", "Role Member")
    owner_membership = await _create_membership(api_client, organization["id"], owner["id"], role="OWNER")
    member_membership = await _create_membership(
        api_client,
        organization["id"],
        member["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "role-owner@example.com")

    response = await api_client.patch(
        f"/organizations/{organization['id']}/memberships/{member_membership['id']}/role",
        json={"role": "ADMIN"},
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == member_membership["id"]
    assert response.json()["role"] == "ADMIN"
    assert response.json()["status"] == "ACTIVE"


@pytest.mark.anyio
async def test_patch_organization_member_status_updates_status_in_active_organization(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Status Org", "status-org")
    owner = await _create_user(api_client, "status-owner@example.com", "Status Owner")
    member = await _create_user(api_client, "status-member@example.com", "Status Member")
    owner_membership = await _create_membership(api_client, organization["id"], owner["id"], role="OWNER")
    member_membership = await _create_membership(
        api_client,
        organization["id"],
        member["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "status-owner@example.com")

    response = await api_client.patch(
        f"/organizations/{organization['id']}/memberships/{member_membership['id']}/status",
        json={"status": "DISABLED"},
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == member_membership["id"]
    assert response.json()["status"] == "DISABLED"
    assert response.json()["is_active"] is False


@pytest.mark.anyio
async def test_patch_organization_member_role_rejects_cross_organization_target(
    api_client: AsyncClient,
) -> None:
    first_organization = await _create_organization(api_client, "Cross Alpha", "cross-alpha")
    second_organization = await _create_organization(api_client, "Cross Beta", "cross-beta")
    owner = await _create_user(api_client, "cross-owner@example.com", "Cross Owner")
    outsider = await _create_user(api_client, "cross-outsider@example.com", "Cross Outsider")
    owner_membership = await _create_membership(
        api_client,
        first_organization["id"],
        owner["id"],
        role="OWNER",
    )
    outsider_membership = await _create_membership(
        api_client,
        second_organization["id"],
        outsider["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "cross-owner@example.com")

    response = await api_client.patch(
        f"/organizations/{first_organization['id']}/memberships/{outsider_membership['id']}/role",
        json={"role": "ADMIN"},
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_organization_members_returns_403_for_member_without_permission(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Permissions Org", "permissions-org")
    owner = await _create_user(api_client, "permissions-owner@example.com", "Permissions Owner")
    member = await _create_user(api_client, "permissions-member@example.com", "Permissions Member")
    await _create_membership(api_client, organization["id"], owner["id"], role="OWNER")
    member_membership = await _create_membership(
        api_client,
        organization["id"],
        member["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "permissions-member@example.com")

    response = await api_client.get(
        f"/organizations/{organization['id']}/memberships",
        headers=_membership_headers(auth_payload["access_token"], member_membership["id"]),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Membership role 'MEMBER' is not allowed to perform 'VIEW_MEMBERS'."
    )


@pytest.mark.anyio
async def test_patch_organization_member_role_prevents_removing_last_owner(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Owner Guard", "owner-guard")
    owner = await _create_user(api_client, "last-owner@example.com", "Last Owner")
    owner_membership = await _create_membership(
        api_client,
        organization["id"],
        owner["id"],
        role="OWNER",
    )
    auth_payload = await _login(api_client, "last-owner@example.com")

    response = await api_client.patch(
        f"/organizations/{organization['id']}/memberships/{owner_membership['id']}/role",
        json={"role": "ADMIN"},
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The last active owner cannot lose the OWNER role."
