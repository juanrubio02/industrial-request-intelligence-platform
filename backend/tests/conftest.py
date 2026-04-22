import asyncio
import os
import re
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.settings import get_settings
from app.infrastructure.database.session import dispose_session_state
from app.infrastructure.database.session import reset_session_state
from app.infrastructure.database.session import get_db_session
from app.infrastructure.storage.local import LocalDocumentStorage
from app.interfaces.http.app import create_app
from app.interfaces.http.dependencies import get_document_processing_dispatcher
from app.interfaces.http.dependencies import get_document_storage
from app.application.documents.processing import DocumentProcessingDispatcher
from tests.settings import get_test_settings

API_PREFIX = "/api/v1"
BOOTSTRAP_MEMBERSHIPS_PATTERN = re.compile(
    r"^/organizations/[^/]+/memberships$"
)


def _run_async(coro):
    return asyncio.run(coro)


async def _wait_for_database(database_url: str) -> None:
    last_error: Exception | None = None

    for _ in range(30):
        engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            poolclass=NullPool,
        )
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(1)
        finally:
            await engine.dispose()

    raise RuntimeError("Test PostgreSQL is not available.") from last_error


async def _reset_database(database_url: str) -> None:
    engine = create_async_engine(
        database_url,
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as connection:
            await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
            await connection.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            await connection.execute(text("GRANT ALL ON SCHEMA public TO public"))
    finally:
        await engine.dispose()


def _apply_migrations(database_url: str) -> None:
    backend_root = Path(__file__).resolve().parents[1]
    alembic_config = Config(str(backend_root / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(backend_root / "alembic"))
    alembic_config.set_main_option("prepend_sys_path", str(backend_root))
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url

    try:
        command.upgrade(alembic_config, "head")
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url


@pytest.fixture(scope="session", autouse=True)
def test_environment() -> Iterator[None]:
    settings = get_test_settings()
    previous_auth_secret_key = os.environ.get("AUTH_SECRET_KEY")
    previous_bootstrap_api_key = os.environ.get("BOOTSTRAP_API_KEY")
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["AUTH_SECRET_KEY"] = settings.auth_secret_key
    os.environ["BOOTSTRAP_API_KEY"] = settings.bootstrap_api_key
    os.environ["DATABASE_URL"] = settings.test_database_url
    get_settings.cache_clear()
    reset_session_state()

    try:
        yield
    finally:
        if previous_auth_secret_key is None:
            os.environ.pop("AUTH_SECRET_KEY", None)
        else:
            os.environ["AUTH_SECRET_KEY"] = previous_auth_secret_key
        if previous_bootstrap_api_key is None:
            os.environ.pop("BOOTSTRAP_API_KEY", None)
        else:
            os.environ["BOOTSTRAP_API_KEY"] = previous_bootstrap_api_key
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
        get_settings.cache_clear()
        reset_session_state()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def migrated_postgres_database() -> str:
    settings = get_test_settings()
    _run_async(_wait_for_database(settings.test_database_url))
    _run_async(_reset_database(settings.test_database_url))
    _apply_migrations(settings.test_database_url)
    return settings.test_database_url


@pytest.fixture
async def db_connection(
    migrated_postgres_database: str,
) -> AsyncIterator[AsyncConnection]:
    await dispose_session_state()
    engine = create_async_engine(
        migrated_postgres_database,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
    connection = await engine.connect()
    transaction = await connection.begin()

    try:
        yield connection
    finally:
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()
        await engine.dispose()
        await dispose_session_state()


@pytest.fixture
async def session_factory(
    db_connection: AsyncConnection,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    yield async_sessionmaker(
        bind=db_connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


@pytest.fixture
def local_document_storage(tmp_path) -> LocalDocumentStorage:
    return LocalDocumentStorage(base_path=tmp_path / "documents")


@pytest.fixture
def document_processing_dispatcher_override():
    return None


class NoOpDocumentProcessingDispatcher(DocumentProcessingDispatcher):
    async def enqueue(self, document_id, organization_id) -> None:
        return None


@pytest.fixture
async def api_client(
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage: LocalDocumentStorage,
    document_processing_dispatcher_override,
) -> AsyncIterator["ApiTestClient"]:
    app = create_app()

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_document_storage] = lambda: local_document_storage
    if document_processing_dispatcher_override is not None:
        app.dependency_overrides[get_document_processing_dispatcher] = (
            lambda: document_processing_dispatcher_override
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield ApiTestClient(
            client=client,
            bootstrap_api_key=get_test_settings().bootstrap_api_key,
        )

    app.dependency_overrides.clear()


@pytest.fixture
async def raw_api_client(
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage: LocalDocumentStorage,
    document_processing_dispatcher_override,
) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_document_storage] = lambda: local_document_storage
    if document_processing_dispatcher_override is not None:
        app.dependency_overrides[get_document_processing_dispatcher] = (
            lambda: document_processing_dispatcher_override
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


class ApiTestResponse:
    def __init__(self, response) -> None:
        self._response = response

    def json(self):
        payload = self._response.json()
        if self._response.is_success:
            if isinstance(payload, dict) and "data" in payload:
                return payload["data"]
            if isinstance(payload, dict) and {"items", "total", "limit", "offset"}.issubset(payload):
                return payload["items"]
            return payload

        if isinstance(payload, dict) and "error" in payload:
            error = payload["error"]
            return {
                "detail": error.get("message"),
                "type": error.get("type"),
                "request_id": error.get("request_id"),
                "details": error.get("details"),
            }

        return payload

    def __getattr__(self, item):
        return getattr(self._response, item)


class ApiTestClient:
    def __init__(self, client: AsyncClient, bootstrap_api_key: str) -> None:
        self._client = client
        self._bootstrap_api_key = bootstrap_api_key

    def _prefix(self, path: str) -> str:
        if path.startswith(API_PREFIX):
            return path
        return f"{API_PREFIX}{path}"

    def _rewrite(self, method: str, path: str, kwargs: dict) -> tuple[str, dict]:
        headers = dict(kwargs.get("headers") or {})
        has_auth = "Authorization" in headers

        if method.upper() == "POST" and not has_auth:
            if path == "/users":
                headers["X-Bootstrap-Key"] = self._bootstrap_api_key
                kwargs["headers"] = headers
                return self._prefix("/bootstrap/users"), kwargs

            if path == "/organizations":
                headers["X-Bootstrap-Key"] = self._bootstrap_api_key
                kwargs["headers"] = headers
                return self._prefix("/bootstrap/organizations"), kwargs

            if BOOTSTRAP_MEMBERSHIPS_PATTERN.match(path):
                headers["X-Bootstrap-Key"] = self._bootstrap_api_key
                kwargs["headers"] = headers
                return self._prefix(f"/bootstrap{path}"), kwargs

        kwargs["headers"] = headers
        return self._prefix(path), kwargs

    async def request(self, method: str, url: str, **kwargs):
        rewritten_url, rewritten_kwargs = self._rewrite(method, url, kwargs)
        response = await self._client.request(method, rewritten_url, **rewritten_kwargs)
        return ApiTestResponse(response)

    async def get(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self.request("POST", url, **kwargs)

    async def patch(self, url: str, **kwargs):
        return await self.request("PATCH", url, **kwargs)

    async def put(self, url: str, **kwargs):
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs):
        return await self.request("DELETE", url, **kwargs)

    @property
    def cookies(self):
        return self._client.cookies
