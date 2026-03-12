from pydantic import BaseModel, ConfigDict, Field

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


class CreateRequestRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    source: RequestSource


class TransitionRequestStatusRequest(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    new_status: RequestStatus
