from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    test_database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@127.0.0.1:55433/industrial_requests_test",
        alias="TEST_DATABASE_URL",
    )
    auth_secret_key: str = Field(default="test-auth-secret", alias="AUTH_SECRET_KEY")


@lru_cache(maxsize=1)
def get_test_settings() -> TestSettings:
    return TestSettings()
