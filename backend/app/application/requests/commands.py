from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


class CreateRequestCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    source: RequestSource
    created_by_membership_id: UUID
    customer_id: UUID | None = None


class UpdateRequestCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    customer_id: UUID | None = None
    membership_id: UUID
    user_id: UUID


class TransitionRequestStatusCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    organization_id: UUID
    membership_id: UUID
    user_id: UUID
    new_status: RequestStatus


class AssignRequestCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    organization_id: UUID
    membership_id: UUID
    assigned_membership_id: UUID


class ListRequestsFilters(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    q: str | None = Field(default=None, max_length=255)
    status: RequestStatus | None = None
    customer_id: UUID | None = None
    assigned_membership_id: UUID | None = None
    source: RequestSource | None = None
