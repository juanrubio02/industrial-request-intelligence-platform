from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth_sessions.entities import AuthSession
from app.domain.auth_sessions.repositories import AuthSessionRepository
from app.infrastructure.database.models.auth_session import AuthSessionModel


class SqlAlchemyAuthSessionRepository(AuthSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, auth_session: AuthSession) -> AuthSession:
        self._session.add(self._to_model(auth_session))
        await self._session.commit()
        return auth_session

    async def get_by_id(self, auth_session_id: UUID) -> AuthSession | None:
        model = await self._session.get(AuthSessionModel, auth_session_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def rotate(
        self,
        *,
        current_session_id: UUID,
        replacement_session: AuthSession,
        revoked_at: datetime,
    ) -> AuthSession:
        result = await self._session.execute(
            select(AuthSessionModel)
            .where(AuthSessionModel.id == current_session_id)
            .with_for_update()
        )
        current_session = result.scalar_one_or_none()
        if current_session is None:
            raise ValueError(f"Auth session '{current_session_id}' was not found.")
        if current_session.revoked_at is not None:
            raise ValueError(f"Auth session '{current_session_id}' is no longer active.")

        self._session.add(self._to_model(replacement_session))
        await self._session.flush()
        current_session.revoked_at = revoked_at
        current_session.replaced_by_session_id = replacement_session.id
        current_session.updated_at = revoked_at
        await self._session.commit()
        return replacement_session

    async def revoke(
        self,
        auth_session_id: UUID,
        *,
        revoked_at: datetime,
    ) -> None:
        await self._session.execute(
            update(AuthSessionModel)
            .where(AuthSessionModel.id == auth_session_id)
            .values(
                revoked_at=revoked_at,
                updated_at=revoked_at,
            )
        )
        await self._session.commit()

    async def revoke_all_by_user_id(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
    ) -> int:
        result = await self._session.execute(
            update(AuthSessionModel)
            .where(
                AuthSessionModel.user_id == user_id,
                AuthSessionModel.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at,
                updated_at=revoked_at,
            )
        )
        await self._session.commit()
        return int(result.rowcount or 0)

    @staticmethod
    def _to_domain(model: AuthSessionModel) -> AuthSession:
        return AuthSession(
            id=model.id,
            user_id=model.user_id,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            replaced_by_session_id=model.replaced_by_session_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(auth_session: AuthSession) -> AuthSessionModel:
        return AuthSessionModel(
            id=auth_session.id,
            user_id=auth_session.user_id,
            expires_at=auth_session.expires_at,
            revoked_at=auth_session.revoked_at,
            replaced_by_session_id=auth_session.replaced_by_session_id,
            created_at=auth_session.created_at,
            updated_at=auth_session.updated_at,
        )
