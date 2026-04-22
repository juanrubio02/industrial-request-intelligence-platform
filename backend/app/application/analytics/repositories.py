from datetime import datetime
from abc import ABC, abstractmethod
from uuid import UUID

from app.application.analytics.schemas import PipelineAnalyticsSnapshot


class PipelineAnalyticsRepository(ABC):
    @abstractmethod
    async def get_pipeline_snapshot(
        self,
        organization_id: UUID,
        *,
        as_of: datetime,
    ) -> PipelineAnalyticsSnapshot:
        raise NotImplementedError
