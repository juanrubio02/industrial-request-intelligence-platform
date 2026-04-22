from datetime import UTC, datetime
from uuid import UUID

from app.application.analytics.repositories import PipelineAnalyticsRepository
from app.application.analytics.schemas import (
    PipelineAnalyticsReadModel,
    PipelineBottleneckReadModel,
)
from app.domain.requests.statuses import RequestStatus
from app.domain.requests.transitions import REQUEST_STATUS_TRANSITION_ORDER


class PipelineAnalyticsService:
    def __init__(
        self,
        pipeline_analytics_repository: PipelineAnalyticsRepository,
        *,
        bottleneck_threshold_days: float,
    ) -> None:
        self._pipeline_analytics_repository = pipeline_analytics_repository
        self._bottleneck_threshold_days = bottleneck_threshold_days

    async def get_pipeline_analytics(
        self,
        organization_id: UUID,
        *,
        as_of: datetime | None = None,
    ) -> PipelineAnalyticsReadModel:
        effective_as_of = as_of or datetime.now(UTC)
        snapshot = await self._pipeline_analytics_repository.get_pipeline_snapshot(
            organization_id,
            as_of=effective_as_of,
        )
        requests_by_status = {
            status: snapshot.requests_by_status.get(status, 0)
            for status in REQUEST_STATUS_TRANSITION_ORDER
        }
        avg_time_per_stage = {
            status: round(snapshot.avg_time_per_stage.get(status, 0.0), 4)
            for status in REQUEST_STATUS_TRANSITION_ORDER
        }
        total_requests = snapshot.total_requests
        conversion_rate = self._safe_ratio(
            requests_by_status[RequestStatus.WON],
            total_requests,
        )
        loss_rate = self._safe_ratio(
            requests_by_status[RequestStatus.LOST],
            total_requests,
        )
        bottlenecks = [
            PipelineBottleneckReadModel(
                status=status,
                avg_days=avg_time_per_stage[status],
            )
            for status in REQUEST_STATUS_TRANSITION_ORDER
            if avg_time_per_stage[status] > self._bottleneck_threshold_days
        ]

        return PipelineAnalyticsReadModel(
            total_requests=total_requests,
            conversion_rate=conversion_rate,
            loss_rate=loss_rate,
            requests_by_status=requests_by_status,
            avg_time_per_stage=avg_time_per_stage,
            pipeline_velocity_days=round(snapshot.pipeline_velocity_days, 4),
            bottlenecks=bottlenecks,
        )

    @staticmethod
    def _safe_ratio(numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0

        return round(numerator / denominator, 4)
