from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = Field(default="forgeflow-request-intelligence-platform", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="APP_CORS_ALLOWED_ORIGINS",
    )
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    documents_storage_path: str = Field(default="storage/documents", alias="DOCUMENTS_STORAGE_PATH")
    auth_secret_key: str = Field(
        default="change-this-auth-secret-in-production",
        alias="AUTH_SECRET_KEY",
    )
    auth_access_token_ttl_seconds: int = Field(
        default=900,
        alias="AUTH_ACCESS_TOKEN_TTL_SECONDS",
    )
    auth_refresh_token_ttl_seconds: int = Field(
        default=604800,
        alias="AUTH_REFRESH_TOKEN_TTL_SECONDS",
    )
    auth_session_cookie_name: str = Field(
        default="iri_session",
        alias="AUTH_SESSION_COOKIE_NAME",
    )
    auth_refresh_cookie_name: str = Field(
        default="iri_refresh",
        alias="AUTH_REFRESH_COOKIE_NAME",
    )
    auth_session_cookie_samesite: str = Field(
        default="lax",
        alias="AUTH_SESSION_COOKIE_SAMESITE",
    )
    auth_session_cookie_secure: bool | None = Field(
        default=None,
        alias="AUTH_SESSION_COOKIE_SECURE",
    )
    analytics_pipeline_bottleneck_threshold_days: float = Field(
        default=3.0,
        alias="ANALYTICS_PIPELINE_BOTTLENECK_THRESHOLD_DAYS",
    )
    bootstrap_api_key: str = Field(
        default="change-this-bootstrap-key",
        alias="BOOTSTRAP_API_KEY",
    )

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="forgeflow_requests", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        if self.app_env.lower() in {"production", "staging"} and (
            self.auth_secret_key == "change-this-auth-secret-in-production"
        ):
            raise ValueError(
                "AUTH_SECRET_KEY must be changed before running in staging or production."
            )
        if self.app_env.lower() in {"production", "staging"} and (
            self.bootstrap_api_key == "change-this-bootstrap-key"
        ):
            raise ValueError(
                "BOOTSTRAP_API_KEY must be changed before running in staging or production."
            )

        if self.auth_session_cookie_samesite.lower() not in {"lax", "strict", "none"}:
            raise ValueError(
                "AUTH_SESSION_COOKIE_SAMESITE must be one of: lax, strict, none."
            )

        cookie_secure_enabled = (
            self.auth_session_cookie_secure
            if self.auth_session_cookie_secure is not None
            else self.app_env.lower() in {"production", "staging"}
        )
        if self.auth_session_cookie_samesite.lower() == "none" and not cookie_secure_enabled:
            raise ValueError(
                "AUTH_SESSION_COOKIE_SECURE must be true when AUTH_SESSION_COOKIE_SAMESITE=none."
            )

        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override

        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.app_cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def documents_storage_dir(self) -> Path:
        return Path(self.documents_storage_path)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def auth_session_cookie_secure_enabled(self) -> bool:
        if self.auth_session_cookie_secure is not None:
            return self.auth_session_cookie_secure

        return self.app_env.lower() in {"production", "staging"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
