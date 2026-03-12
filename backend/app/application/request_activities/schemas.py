from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.request_activities.types import RequestActivityType


class RequestActivityReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    request_id: UUID
    organization_id: UUID
    membership_id: UUID
    type: RequestActivityType
    payload: dict[str, Any]
    created_at: datetime
