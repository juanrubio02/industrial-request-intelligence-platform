from fastapi import Response

from app.core.settings import Settings


def set_auth_session_cookie(
    response: Response,
    *,
    settings: Settings,
    access_token: str,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key=settings.auth_session_cookie_name,
        value=access_token,
        max_age=settings.auth_access_token_ttl_seconds,
        httponly=True,
        secure=settings.auth_session_cookie_secure_enabled,
        samesite=settings.auth_session_cookie_samesite.lower(),
        path="/",
    )
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        max_age=settings.auth_refresh_token_ttl_seconds,
        httponly=True,
        secure=settings.auth_session_cookie_secure_enabled,
        samesite=settings.auth_session_cookie_samesite.lower(),
        path="/",
    )


def clear_auth_session_cookie(
    response: Response,
    *,
    settings: Settings,
) -> None:
    response.delete_cookie(
        key=settings.auth_session_cookie_name,
        path="/",
    )
    response.delete_cookie(
        key=settings.auth_refresh_cookie_name,
        path="/",
    )
