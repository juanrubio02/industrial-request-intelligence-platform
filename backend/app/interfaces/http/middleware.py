import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.interfaces.http.logging import bind_log_context
from app.interfaces.http.logging import clear_log_context
from app.interfaces.http.logging import log_event


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started_at = time.perf_counter()
        request_id = str(uuid4())
        request.state.request_id = request_id
        request.state.started_at = started_at
        request.state.authenticated_user_id = None
        request.state.access_token = None
        request.state.active_membership_id = None
        request.state.organization_id = None
        bind_log_context(
            request_id=request_id,
            user_id=None,
            membership_id=None,
            organization_id=None,
            job_id=None,
            path=request.url.path,
            method=request.method,
            status_code=None,
            latency_ms=None,
            error_type=None,
        )

        try:
            response = await call_next(request)
        except Exception:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
            log_event(
                logging.ERROR,
                {
                    "request_id": request_id,
                    "user_id": request.state.authenticated_user_id,
                    "membership_id": request.state.active_membership_id,
                    "organization_id": getattr(request.state, "organization_id", None),
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "latency_ms": latency_ms,
                    "error_type": "UnhandledException",
                },
            )
            clear_log_context()
            raise

        latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
        response.headers["X-Request-Id"] = request_id
        log_event(
            logging.INFO,
            {
                "request_id": request_id,
                "user_id": request.state.authenticated_user_id,
                "membership_id": request.state.active_membership_id,
                "organization_id": getattr(request.state, "organization_id", None),
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "error_type": None,
            },
        )
        clear_log_context()
        return response
