from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.auth_sessions.entities import AuthSession


class AuthSessionRepository(ABC):
    @abstractmethod
    async def add(self, auth_session: AuthSession) -> AuthSession:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, auth_session_id: UUID) -> AuthSession | None:
        raise NotImplementedError

    @abstractmethod
    async def rotate(
        self,
        *,
        current_session_id: UUID,
        replacement_session: AuthSession,
        revoked_at: datetime,
    ) -> AuthSession:
        raise NotImplementedError

    @abstractmethod
    async def revoke(
        self,
        auth_session_id: UUID,
        *,
        revoked_at: datetime,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_all_by_user_id(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
    ) -> int:
        raise NotImplementedError
