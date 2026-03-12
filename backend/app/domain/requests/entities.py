from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


@dataclass(frozen=True, slots=True)
class Request:
    id: UUID
    organization_id: UUID
    title: str
    description: str | None
    status: RequestStatus
    source: RequestSource
    created_by_membership_id: UUID
    created_at: datetime
    updated_at: datetime

