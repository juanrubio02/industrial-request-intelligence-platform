from fastapi import APIRouter, Depends

from app.application.health.schemas import HealthStatus
from app.interfaces.http.dependencies import get_health_service
from app.interfaces.http.responses import success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=ApiSuccessResponse[HealthStatus],
    summary="Health check",
)
async def healthcheck(
    health_service=Depends(get_health_service),
) -> ApiSuccessResponse[HealthStatus]:
    return success_response(health_service.get_status())
