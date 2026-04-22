from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiSuccessResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(frozen=True)

    data: T


class ApiErrorDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str
    message: str
    request_id: str | None = None
    details: list[dict[str, object]] | None = None


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    error: ApiErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(frozen=True)

    items: list[T]
    total: int
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class MessageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    message: str
