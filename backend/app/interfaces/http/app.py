from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import get_settings
from app.interfaces.http.api.router import api_router
from app.interfaces.http.errors import register_exception_handlers
from app.interfaces.http.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
    )
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins_list,
        allow_credentials=True,
        # Allow PATCH/PUT/DELETE for API mutations (assignment, verified data, etc.)
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Membership-Id"],
    )
    register_exception_handlers(application)
    application.include_router(api_router)
    return application
