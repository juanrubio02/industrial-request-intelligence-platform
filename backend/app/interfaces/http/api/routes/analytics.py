from fastapi import APIRouter, Depends

from app.application.analytics.schemas import PipelineAnalyticsReadModel
from app.application.auth.authorization import MembershipPermission
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.interfaces.http.dependencies import (
    get_service_factory,
    require_membership_permission,
)
from app.interfaces.http.responses import success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse
from app.interfaces.http.services import ServiceFactory

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/pipeline",
    response_model=ApiSuccessResponse[PipelineAnalyticsReadModel],
)
async def get_pipeline_analytics(
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_ANALYTICS)
    ),
) -> ApiSuccessResponse[PipelineAnalyticsReadModel]:
    return success_response(
        await services.pipeline_analytics_service.get_pipeline_analytics(
            current_membership.organization_id
        )
    )
