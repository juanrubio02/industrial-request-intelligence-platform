from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.domain.users.entities import User


class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_ids(self, user_ids: Sequence[UUID]) -> list[User]:
        raise NotImplementedError
