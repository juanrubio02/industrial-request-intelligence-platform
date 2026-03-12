from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.request_activities.types import RequestActivityType


@dataclass(frozen=True, slots=True)
class RequestActivity:
    id: UUID
    request_id: UUID
    organization_id: UUID
    membership_id: UUID
    type: RequestActivityType
    payload: dict[str, Any]
    created_at: datetime

