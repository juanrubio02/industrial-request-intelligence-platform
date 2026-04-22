from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RefreshTokenClaims:
    token_id: UUID
    user_id: UUID
    expires_at: datetime


class TokenService(ABC):
    @abstractmethod
    def issue_access_token(self, user_id: UUID) -> str:
        raise NotImplementedError

    @abstractmethod
    def issue_refresh_token(self, user_id: UUID, token_id: UUID) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify_access_token(self, token: str) -> UUID:
        raise NotImplementedError

    @abstractmethod
    def verify_refresh_token(self, token: str) -> RefreshTokenClaims:
        raise NotImplementedError
