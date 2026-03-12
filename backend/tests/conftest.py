import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import get_settings
from app.infrastructure.database.session import get_db_session
from app.infrastructure.storage.local import LocalDocumentStorage
from app.interfaces.http.app import create_app
from app.interfaces.http.dependencies import get_document_processing_dispatcher
from app.interfaces.http.dependencies import get_document_storage
from tests.settings import get_test_settings


def _run_async(coro):
    return asyncio.run(coro)


async def _wait_for_database(database_url: str) -> None:
    last_error: Exception | None = None

    for _ in range(30):
        engine = create_async_engine(database_url, pool_pre_ping=True)
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
    engine = create_async_engine(database_url, isolation_level="AUTOCOMMIT")

    try:
        async with engine.connect() as connection:
            await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
            await connection.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            await connection.execute(text("GRANT ALL ON SCHEMA public TO public"))
    finally:
        await engine.dispose()


def _apply_migrations(database_url: str) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
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
    os.environ["AUTH_SECRET_KEY"] = settings.auth_secret_key
    get_settings.cache_clear()

    try:
        yield
    finally:
        if previous_auth_secret_key is None:
            os.environ.pop("AUTH_SECRET_KEY", None)
        else:
            os.environ["AUTH_SECRET_KEY"] = previous_auth_secret_key
        get_settings.cache_clear()


@pytest.fixture(scope="session")
def migrated_postgres_database() -> str:
    settings = get_test_settings()
    _run_async(_wait_for_database(settings.test_database_url))
    _run_async(_reset_database(settings.test_database_url))
    _apply_migrations(settings.test_database_url)
    return settings.test_database_url


@pytest.fixture
async def session_factory(
    migrated_postgres_database: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        migrated_postgres_database,
        pool_pre_ping=True,
    )

    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE request_activities, document_processing_results, documents, requests, "
                "organization_memberships, users, organizations "
                "RESTART IDENTITY CASCADE"
            )
        )

    try:
        yield async_sessionmaker(
            bind=engine,
            autoflush=False,
            expire_on_commit=False,
        )
    finally:
        await engine.dispose()


@pytest.fixture
def local_document_storage(tmp_path) -> LocalDocumentStorage:
    return LocalDocumentStorage(base_path=tmp_path / "documents")


@pytest.fixture
def document_processing_dispatcher_override():
    return None


@pytest.fixture
async def api_client(
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage: LocalDocumentStorage,
    document_processing_dispatcher_override,
) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_document_storage] = lambda: local_document_storage
    if document_processing_dispatcher_override is not None:
        app.dependency_overrides[get_document_processing_dispatcher] = (
            lambda: document_processing_dispatcher_override
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
