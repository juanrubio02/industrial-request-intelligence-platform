from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


class RequestReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    title: str
    description: str | None
    status: RequestStatus
    source: RequestSource
    created_by_membership_id: UUID
    created_at: datetime
    updated_at: datetime

