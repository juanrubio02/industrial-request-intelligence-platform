from typing import TypeVar

from app.application.common.pagination import PaginatedResult
from app.interfaces.http.schemas.common import ApiSuccessResponse, PaginatedResponse

T = TypeVar("T")


def success_response(data: T) -> ApiSuccessResponse[T]:
    return ApiSuccessResponse[T](data=data)


def paginated_response(result: PaginatedResult[T]) -> PaginatedResponse[T]:
    return PaginatedResponse[T](
        items=result.items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )
