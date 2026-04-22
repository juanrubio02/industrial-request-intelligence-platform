from typing import Annotated

from fastapi import Depends, Query

from app.application.common.pagination import PaginationParams


def get_pagination_params(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


Pagination = Annotated[PaginationParams, Depends(get_pagination_params)]
