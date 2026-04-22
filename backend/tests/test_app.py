import pytest
from httpx import ASGITransport, AsyncClient

from app.interfaces.http.app import create_app


def test_create_app_returns_fastapi_instance() -> None:
    created_app = create_app()

    assert created_app.title == "forgeflow-request-intelligence-platform"


@pytest.mark.anyio
async def test_app_starts_and_exposes_openapi() -> None:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
