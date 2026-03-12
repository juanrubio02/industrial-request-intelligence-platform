import pytest
from httpx import ASGITransport, AsyncClient

from app.interfaces.http.app import create_app


@pytest.mark.anyio
async def test_healthcheck_endpoint_returns_ok_status() -> None:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "industrial-request-intelligence-platform",
        "environment": "local",
    }
