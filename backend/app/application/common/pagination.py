from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class PaginationParams:
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True, slots=True)
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
