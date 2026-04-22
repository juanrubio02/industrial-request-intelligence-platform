from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.request_activities.types import RequestActivityType


class RequestActivityActorReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    membership_id: UUID
    user_id: UUID | None = None


class RequestActivityReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    request_id: UUID
    organization_id: UUID
    membership_id: UUID
    type: RequestActivityType
    actor: RequestActivityActorReadModel
    payload: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime
