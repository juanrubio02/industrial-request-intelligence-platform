from fastapi import APIRouter, Depends, status

from app.application.auth.authorization import MembershipPermission
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.application.demo_intake.schemas import (
    DemoIntakeRunResultReadModel,
    DemoIntakeScenarioReadModel,
)
from app.interfaces.http.dependencies import (
    get_service_factory,
    require_membership_permission,
)
from app.interfaces.http.pagination import Pagination
from app.interfaces.http.responses import paginated_response, success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse, PaginatedResponse
from app.interfaces.http.services import ServiceFactory

router = APIRouter(prefix="/demo/intake", tags=["demo-intake"])


@router.get(
    "/scenarios",
    response_model=PaginatedResponse[DemoIntakeScenarioReadModel],
)
async def list_demo_intake_scenarios(
    pagination: Pagination,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_REQUEST)
    ),
) -> PaginatedResponse[DemoIntakeScenarioReadModel]:
    result = services.list_demo_intake_scenarios_use_case.execute(pagination)
    return paginated_response(result)


@router.post(
    "/scenarios/{scenario_key}/run",
    response_model=ApiSuccessResponse[DemoIntakeRunResultReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def run_demo_intake_scenario(
    scenario_key: str,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_REQUEST)
    ),
) -> ApiSuccessResponse[DemoIntakeRunResultReadModel]:
    return success_response(
        await services.run_demo_intake_scenario_use_case.execute(
            scenario_key=scenario_key,
            organization_id=current_membership.organization_id,
            membership_id=current_membership.id,
        )
    )
