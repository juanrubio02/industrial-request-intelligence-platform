from uuid import UUID

import pytest
from httpx import AsyncClient


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

    response = await api_client.get(f"/organizations/{organization_id}")

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
    response = await api_client.get("/organizations/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
