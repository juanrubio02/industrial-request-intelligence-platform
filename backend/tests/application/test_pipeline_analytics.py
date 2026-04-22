from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.analytics.pipeline_analytics_service import (
    PipelineAnalyticsService,
)
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus
from app.infrastructure.analytics.repositories import SqlAlchemyPipelineAnalyticsRepository
from app.infrastructure.database.models.organization import OrganizationModel
from app.infrastructure.database.models.organization_membership import (
    OrganizationMembershipModel,
)
from app.infrastructure.database.models.request import RequestModel
from app.infrastructure.database.models.request_status_history import (
    RequestStatusHistoryModel,
)
from app.infrastructure.database.models.user import UserModel


async def _seed_pipeline_history(session: AsyncSession):
    organization_id = uuid4()
    owner_user_id = uuid4()
    owner_membership_id = uuid4()

    session.add(
        OrganizationModel(
            id=organization_id,
            name="Analytics Org",
            slug="analytics-org",
            is_active=True,
        )
    )
    session.add(
        UserModel(
            id=owner_user_id,
            email="analytics@example.com",
            full_name="Analytics User",
            password_hash="hashed-password",
            is_active=True,
        )
    )
    await session.flush()
    session.add(
        OrganizationMembershipModel(
            id=owner_membership_id,
            organization_id=organization_id,
            user_id=owner_user_id,
            role=OrganizationMembershipRole.ADMIN,
            joined_at=datetime(2026, 3, 1, tzinfo=UTC),
            is_active=True,
        )
    )

    request_won_id = uuid4()
    request_lost_id = uuid4()
    request_active_id = uuid4()

    session.add_all(
        [
            RequestModel(
                id=request_won_id,
                organization_id=organization_id,
                title="Won request",
                description=None,
                status=RequestStatus.WON,
                source=RequestSource.EMAIL,
                created_by_membership_id=owner_membership_id,
                assigned_membership_id=owner_membership_id,
                created_at=datetime(2026, 3, 1, tzinfo=UTC),
                updated_at=datetime(2026, 3, 12, tzinfo=UTC),
            ),
            RequestModel(
                id=request_lost_id,
                organization_id=organization_id,
                title="Lost request",
                description=None,
                status=RequestStatus.LOST,
                source=RequestSource.MANUAL,
                created_by_membership_id=owner_membership_id,
                assigned_membership_id=None,
                created_at=datetime(2026, 3, 2, tzinfo=UTC),
                updated_at=datetime(2026, 3, 9, tzinfo=UTC),
            ),
            RequestModel(
                id=request_active_id,
                organization_id=organization_id,
                title="Active request",
                description=None,
                status=RequestStatus.QUOTE_PREPARING,
                source=RequestSource.API,
                created_by_membership_id=owner_membership_id,
                assigned_membership_id=owner_membership_id,
                created_at=datetime(2026, 3, 5, tzinfo=UTC),
                updated_at=datetime(2026, 3, 9, tzinfo=UTC),
            ),
        ]
    )

    def history_entry(
        *,
        request_id,
        previous_status,
        new_status,
        changed_at,
    ) -> RequestStatusHistoryModel:
        return RequestStatusHistoryModel(
            id=uuid4(),
            request_id=request_id,
            organization_id=organization_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_at=changed_at,
            changed_by=owner_membership_id,
            changed_by_user_id=owner_user_id,
        )

    session.add_all(
        [
            history_entry(
                request_id=request_won_id,
                previous_status=None,
                new_status=RequestStatus.NEW,
                changed_at=datetime(2026, 3, 1, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_won_id,
                previous_status=RequestStatus.NEW,
                new_status=RequestStatus.UNDER_REVIEW,
                changed_at=datetime(2026, 3, 3, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_won_id,
                previous_status=RequestStatus.UNDER_REVIEW,
                new_status=RequestStatus.QUOTE_PREPARING,
                changed_at=datetime(2026, 3, 6, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_won_id,
                previous_status=RequestStatus.QUOTE_PREPARING,
                new_status=RequestStatus.QUOTE_SENT,
                changed_at=datetime(2026, 3, 8, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_won_id,
                previous_status=RequestStatus.QUOTE_SENT,
                new_status=RequestStatus.NEGOTIATION,
                changed_at=datetime(2026, 3, 10, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_won_id,
                previous_status=RequestStatus.NEGOTIATION,
                new_status=RequestStatus.WON,
                changed_at=datetime(2026, 3, 12, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_lost_id,
                previous_status=None,
                new_status=RequestStatus.NEW,
                changed_at=datetime(2026, 3, 2, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_lost_id,
                previous_status=RequestStatus.NEW,
                new_status=RequestStatus.UNDER_REVIEW,
                changed_at=datetime(2026, 3, 4, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_lost_id,
                previous_status=RequestStatus.UNDER_REVIEW,
                new_status=RequestStatus.QUOTE_PREPARING,
                changed_at=datetime(2026, 3, 5, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_lost_id,
                previous_status=RequestStatus.QUOTE_PREPARING,
                new_status=RequestStatus.QUOTE_SENT,
                changed_at=datetime(2026, 3, 7, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_lost_id,
                previous_status=RequestStatus.QUOTE_SENT,
                new_status=RequestStatus.LOST,
                changed_at=datetime(2026, 3, 9, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_active_id,
                previous_status=None,
                new_status=RequestStatus.NEW,
                changed_at=datetime(2026, 3, 5, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_active_id,
                previous_status=RequestStatus.NEW,
                new_status=RequestStatus.UNDER_REVIEW,
                changed_at=datetime(2026, 3, 6, tzinfo=UTC),
            ),
            history_entry(
                request_id=request_active_id,
                previous_status=RequestStatus.UNDER_REVIEW,
                new_status=RequestStatus.QUOTE_PREPARING,
                changed_at=datetime(2026, 3, 9, tzinfo=UTC),
            ),
        ]
    )
    await session.commit()
    return organization_id


@pytest.mark.anyio
async def test_pipeline_analytics_service_calculates_rates_and_stage_durations(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        organization_id = await _seed_pipeline_history(session)

    async with session_factory() as session:
        repository = SqlAlchemyPipelineAnalyticsRepository(session=session)
        service = PipelineAnalyticsService(
            pipeline_analytics_repository=repository,
            bottleneck_threshold_days=2.5,
        )

        analytics = await service.get_pipeline_analytics(
            organization_id,
            as_of=datetime(2026, 3, 13, tzinfo=UTC),
        )

    assert analytics.total_requests == 3
    assert analytics.conversion_rate == pytest.approx(0.3333, abs=0.0001)
    assert analytics.loss_rate == pytest.approx(0.3333, abs=0.0001)
    assert analytics.requests_by_status == {
        RequestStatus.NEW: 0,
        RequestStatus.UNDER_REVIEW: 0,
        RequestStatus.QUOTE_PREPARING: 1,
        RequestStatus.QUOTE_SENT: 0,
        RequestStatus.NEGOTIATION: 0,
        RequestStatus.WON: 1,
        RequestStatus.LOST: 1,
    }
    assert analytics.avg_time_per_stage[RequestStatus.NEW] == pytest.approx(
        1.6667,
        abs=0.0001,
    )
    assert analytics.avg_time_per_stage[RequestStatus.UNDER_REVIEW] == pytest.approx(
        2.3333,
        abs=0.0001,
    )
    assert analytics.avg_time_per_stage[RequestStatus.QUOTE_PREPARING] == pytest.approx(
        2.6667,
        abs=0.0001,
    )
    assert analytics.avg_time_per_stage[RequestStatus.QUOTE_SENT] == pytest.approx(
        2.0,
        abs=0.0001,
    )
    assert analytics.avg_time_per_stage[RequestStatus.NEGOTIATION] == pytest.approx(
        2.0,
        abs=0.0001,
    )
    assert analytics.pipeline_velocity_days == pytest.approx(11.0, abs=0.0001)
    assert len(analytics.bottlenecks) == 1
    assert analytics.bottlenecks[0].status == RequestStatus.QUOTE_PREPARING
    assert analytics.bottlenecks[0].avg_days == pytest.approx(2.6667, abs=0.0001)
