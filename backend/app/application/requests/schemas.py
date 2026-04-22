from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


class RequestCustomerSummaryReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str


class RequestReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    customer_id: UUID | None
    customer: RequestCustomerSummaryReadModel | None = None
    title: str
    description: str | None
    status: RequestStatus
    source: RequestSource
    created_by_membership_id: UUID
    assigned_membership_id: UUID | None
    documents_count: int = 0
    comments_count: int = 0
    available_status_transitions: list[RequestStatus] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
