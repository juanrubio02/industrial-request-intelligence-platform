import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_post_users_creates_user(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/users",
        json={
            "email": "alice@example.com",
            "full_name": "Alice Example",
            "password": "StrongPass123!",
        },
    )

    payload = response.json()

    assert response.status_code == 201
    assert payload["email"] == "alice@example.com"
    assert payload["full_name"] == "Alice Example"
    assert payload["is_active"] is True
    assert "password_hash" not in payload
