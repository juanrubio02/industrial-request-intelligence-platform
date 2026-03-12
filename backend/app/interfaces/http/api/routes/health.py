from fastapi import APIRouter

from app.application.health.schemas import HealthStatus
from app.interfaces.http.dependencies import get_health_service

router = APIRouter()


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def healthcheck() -> HealthStatus:
    return get_health_service().get_status()
