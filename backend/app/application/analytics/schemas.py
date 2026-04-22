from pydantic import BaseModel, ConfigDict

from app.domain.requests.statuses import RequestStatus


class PipelineBottleneckReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: RequestStatus
    avg_days: float


class PipelineAnalyticsSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_requests: int
    requests_by_status: dict[RequestStatus, int]
    avg_time_per_stage: dict[RequestStatus, float]
    pipeline_velocity_days: float


class PipelineAnalyticsReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_requests: int
    conversion_rate: float
    loss_rate: float
    requests_by_status: dict[RequestStatus, int]
    avg_time_per_stage: dict[RequestStatus, float]
    pipeline_velocity_days: float
    bottlenecks: list[PipelineBottleneckReadModel]
