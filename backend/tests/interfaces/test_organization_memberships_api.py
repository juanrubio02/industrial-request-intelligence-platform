from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.domain.organization_memberships.roles import OrganizationMembershipRole


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


def _membership_headers(access_token: str, membership_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Membership-Id": membership_id,
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "role",
    [
        OrganizationMembershipRole.OWNER.value,
        OrganizationMembershipRole.ADMIN.value,
        OrganizationMembershipRole.MEMBER.value,
    ],
)
async def test_post_organization_memberships_creates_membership(
    api_client: AsyncClient,
    role: str,
) -> None:
    organization = await _create_organization(api_client, "Acme", "acme")
    user = await _create_user(api_client, "member@example.com", "Member Example")

    response = await api_client.post(
        f"/organizations/{organization['id']}/memberships",
        json={"user_id": user["id"], "role": role},
    )

    payload = response.json()

    assert response.status_code == 201
    assert payload["organization_id"] == organization["id"]
    assert payload["user_id"] == user["id"]
    assert payload["role"] == role
    assert payload["is_active"] is True


@pytest.mark.anyio
async def test_get_organization_membership_returns_membership_in_organization(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Nova", "nova")
    owner = await _create_user(api_client, "nova-owner@example.com", "Nova Owner")
    owner_membership_response = await api_client.post(
        f"/organizations/{organization['id']}/memberships",
        json={"user_id": owner["id"], "role": OrganizationMembershipRole.OWNER.value},
    )
    owner_membership = owner_membership_response.json()
    auth_payload = await _login(api_client, "nova-owner@example.com")
    member_user = await _create_user(api_client, "nova-user@example.com", "Nova User")
    create_membership_response = await api_client.post(
        f"/organizations/{organization['id']}/memberships",
        json={"user_id": member_user["id"], "role": OrganizationMembershipRole.MEMBER.value},
    )
    membership = create_membership_response.json()

    response = await api_client.get(
        f"/organizations/{organization['id']}/memberships/{membership['id']}",
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == membership["id"]
    assert response.json()["organization_id"] == organization["id"]
    assert response.json()["role"] == OrganizationMembershipRole.MEMBER.value


@pytest.mark.anyio
async def test_get_organization_membership_rejects_spoofed_membership_context(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Spoof Members", "spoof-members")
    owner = await _create_user(api_client, "spoof-members-owner@example.com", "Spoof Members Owner")
    intruder = await _create_user(api_client, "spoof-members-intruder@example.com", "Spoof Members Intruder")
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
    auth_payload = await _login(api_client, "spoof-members-owner@example.com")

    response = await api_client.get(
        f"/organizations/{organization['id']}/memberships/{owner_membership['id']}",
        headers=_membership_headers(auth_payload["access_token"], intruder_membership["id"]),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Membership context is invalid."


@pytest.mark.anyio
async def test_post_organization_memberships_returns_conflict_for_duplicate_active_membership(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Helix", "helix-org")
    user = await _create_user(api_client, "helix@example.com", "Helix User")

    first_response = await api_client.post(
        f"/organizations/{organization['id']}/memberships",
        json={"user_id": user["id"], "role": OrganizationMembershipRole.MEMBER.value},
    )
    second_response = await api_client.post(
        f"/organizations/{organization['id']}/memberships",
        json={"user_id": user["id"], "role": OrganizationMembershipRole.ADMIN.value},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "An active membership already exists for this user in the organization."
    )


@pytest.mark.anyio
async def test_post_organization_memberships_returns_not_found_for_missing_organization(
    api_client: AsyncClient,
) -> None:
    user = await _create_user(api_client, "ghost-org@example.com", "Ghost Org User")

    response = await api_client.post(
        f"/organizations/{uuid4()}/memberships",
        json={"user_id": user["id"], "role": OrganizationMembershipRole.MEMBER.value},
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_organization_memberships_returns_not_found_for_missing_user(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Orbit", "orbit")

    response = await api_client.post(
        f"/organizations/{organization['id']}/memberships",
        json={"user_id": str(uuid4()), "role": OrganizationMembershipRole.MEMBER.value},
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_organization_memberships_rejects_invalid_role(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Sigma", "sigma")
    user = await _create_user(api_client, "sigma@example.com", "Sigma User")

    response = await api_client.post(
        f"/organizations/{organization['id']}/memberships",
        json={"user_id": user["id"], "role": "SUPERUSER"},
    )

    assert response.status_code == 422
