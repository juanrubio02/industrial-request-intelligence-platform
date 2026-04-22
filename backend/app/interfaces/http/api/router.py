from fastapi import APIRouter

from app.interfaces.http.api.routes.auth import router as auth_router
from app.interfaces.http.api.routes.analytics import router as analytics_router
from app.interfaces.http.api.routes.bootstrap import router as bootstrap_router
from app.interfaces.http.api.routes.documents import router as documents_router
from app.interfaces.http.api.routes.demo_intake import router as demo_intake_router
from app.interfaces.http.api.routes.health import router as health_router
from app.interfaces.http.api.routes.organization_memberships import router as organization_memberships_router
from app.interfaces.http.api.routes.organizations import router as organizations_router
from app.interfaces.http.api.routes.requests import router as requests_router
from app.interfaces.http.api.routes.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(bootstrap_router)
api_router.include_router(analytics_router)
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(users_router)
api_router.include_router(organization_memberships_router)
api_router.include_router(requests_router)
api_router.include_router(documents_router)
api_router.include_router(demo_intake_router)
