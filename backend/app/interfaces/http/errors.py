import logging
import time

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.interfaces.http.logging import log_event
from app.interfaces.http.schemas.common import ApiErrorResponse


def _build_error_response(
    request: Request,
    *,
    status_code: int,
    error_type: str,
    message: str,
    details: list[dict[str, object]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    started_at = getattr(request.state, "started_at", None)
    latency_ms = (
        round((time.perf_counter() - started_at) * 1000, 3)
        if started_at is not None
        else None
    )
    payload = ApiErrorResponse(
        error={
            "type": error_type,
            "message": message,
            "request_id": getattr(request.state, "request_id", None),
            "details": details,
        }
    )
    log_event(
        logging.WARNING if status_code < 500 else logging.ERROR,
        {
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "authenticated_user_id", None),
            "membership_id": getattr(request.state, "active_membership_id", None),
            "organization_id": getattr(request.state, "organization_id", None),
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "error_type": error_type,
        },
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
        headers=headers,
    )


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(AuthenticationError)
    async def handle_authentication_error(
        request: Request,
        exc: AuthenticationError,
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type=exc.__class__.__name__,
            message=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @application.exception_handler(AuthorizationError)
    async def handle_authorization_error(
        request: Request,
        exc: AuthorizationError,
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type=exc.__class__.__name__,
            message=str(exc),
        )

    @application.exception_handler(ValidationError)
    async def handle_validation_error(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type=exc.__class__.__name__,
            message=str(exc),
        )

    @application.exception_handler(ResourceConflictError)
    async def handle_conflict_error(
        request: Request,
        exc: ResourceConflictError,
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_409_CONFLICT,
            error_type=exc.__class__.__name__,
            message=str(exc),
        )

    @application.exception_handler(ResourceNotFoundError)
    async def handle_not_found_error(
        request: Request,
        exc: ResourceNotFoundError,
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type=exc.__class__.__name__,
            message=str(exc),
        )

    @application.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type=exc.__class__.__name__,
            message="Request validation failed.",
            details=[
                {
                    "loc": list(error.get("loc", ())),
                    "msg": error.get("msg", ""),
                    "type": error.get("type", ""),
                }
                for error in exc.errors()
            ],
        )
