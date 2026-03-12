from abc import ABC, abstractmethod
from uuid import UUID


class AccessTokenService(ABC):
    @abstractmethod
    def issue(self, user_id: UUID) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify(self, token: str) -> UUID:
        raise NotImplementedError
