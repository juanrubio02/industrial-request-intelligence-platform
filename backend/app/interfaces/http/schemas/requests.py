from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


class CreateRequestRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    source: RequestSource
    customer_id: UUID | None = None


class UpdateRequestRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    customer_id: UUID | None = None


class TransitionRequestStatusRequest(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    new_status: RequestStatus


class AssignRequestRequest(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    assigned_membership_id: UUID
