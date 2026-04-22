from datetime import datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.repositories import PipelineAnalyticsRepository
from app.application.analytics.schemas import PipelineAnalyticsSnapshot
from app.domain.requests.statuses import RequestStatus
from app.infrastructure.database.models.request import RequestModel
from app.infrastructure.database.models.request_status_history import (
    RequestStatusHistoryModel,
)


class SqlAlchemyPipelineAnalyticsRepository(PipelineAnalyticsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_pipeline_snapshot(
        self,
        organization_id: UUID,
        *,
        as_of: datetime,
    ) -> PipelineAnalyticsSnapshot:
        status_counts = await self._get_status_counts(organization_id)
        avg_time_per_stage = await self._get_avg_time_per_stage(
            organization_id,
            as_of=as_of,
        )
        pipeline_velocity_days = await self._get_pipeline_velocity_days(organization_id)

        return PipelineAnalyticsSnapshot(
            total_requests=sum(status_counts.values()),
            requests_by_status=status_counts,
            avg_time_per_stage=avg_time_per_stage,
            pipeline_velocity_days=pipeline_velocity_days,
        )

    async def _get_status_counts(
        self,
        organization_id: UUID,
    ) -> dict[RequestStatus, int]:
        statement = (
            select(RequestModel.status, func.count(RequestModel.id))
            .where(RequestModel.organization_id == organization_id)
            .group_by(RequestModel.status)
        )
        result = await self._session.execute(statement)
        return {
            status: count
            for status, count in result.all()
        }

    async def _get_avg_time_per_stage(
        self,
        organization_id: UUID,
        *,
        as_of: datetime,
    ) -> dict[RequestStatus, float]:
        ordered_history = (
            select(
                RequestStatusHistoryModel.request_id.label("request_id"),
                RequestStatusHistoryModel.new_status.label("status"),
                RequestStatusHistoryModel.changed_at.label("changed_at"),
                func.lead(RequestStatusHistoryModel.changed_at)
                .over(
                    partition_by=RequestStatusHistoryModel.request_id,
                    order_by=(
                        RequestStatusHistoryModel.changed_at.asc(),
                        RequestStatusHistoryModel.id.asc(),
                    ),
                )
                .label("next_changed_at"),
            )
            .where(RequestStatusHistoryModel.organization_id == organization_id)
            .subquery()
        )
        stage_end = case(
            (
                ordered_history.c.next_changed_at.is_not(None),
                ordered_history.c.next_changed_at,
            ),
            (
                ordered_history.c.status.in_([RequestStatus.WON, RequestStatus.LOST]),
                ordered_history.c.changed_at,
            ),
            else_=as_of,
        )
        duration_days = (
            func.extract("epoch", stage_end - ordered_history.c.changed_at)
            / 86400.0
        )
        statement = (
            select(
                ordered_history.c.status,
                func.avg(duration_days),
            )
            .group_by(ordered_history.c.status)
        )
        result = await self._session.execute(statement)
        return {
            status: float(avg_days or 0.0)
            for status, avg_days in result.all()
        }

    async def _get_pipeline_velocity_days(
        self,
        organization_id: UUID,
    ) -> float:
        milestones = (
            select(
                RequestStatusHistoryModel.request_id.label("request_id"),
                func.min(
                    case(
                        (
                            RequestStatusHistoryModel.new_status == RequestStatus.NEW,
                            RequestStatusHistoryModel.changed_at,
                        ),
                    )
                ).label("entered_new_at"),
                func.min(
                    case(
                        (
                            RequestStatusHistoryModel.new_status == RequestStatus.WON,
                            RequestStatusHistoryModel.changed_at,
                        ),
                    )
                ).label("entered_won_at"),
            )
            .where(
                RequestStatusHistoryModel.organization_id == organization_id,
                RequestStatusHistoryModel.new_status.in_(
                    [RequestStatus.NEW, RequestStatus.WON]
                ),
            )
            .group_by(RequestStatusHistoryModel.request_id)
            .subquery()
        )
        statement = select(
            func.avg(
                func.extract(
                    "epoch",
                    milestones.c.entered_won_at - milestones.c.entered_new_at,
                )
                / 86400.0
            )
        ).where(
            milestones.c.entered_new_at.is_not(None),
            milestones.c.entered_won_at.is_not(None),
        )
        result = await self._session.execute(statement)
        return float(result.scalar() or 0.0)
