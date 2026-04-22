from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.requests.statuses import RequestStatus


@dataclass(frozen=True, slots=True)
class RequestStatusHistoryEntry:
    id: UUID
    request_id: UUID
    organization_id: UUID
    previous_status: RequestStatus | None
    new_status: RequestStatus
    changed_at: datetime
    changed_by: UUID
    changed_by_user_id: UUID
