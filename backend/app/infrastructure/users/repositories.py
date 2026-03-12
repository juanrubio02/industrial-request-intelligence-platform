from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.users.exceptions import UserEmailAlreadyExistsError
from app.domain.users.entities import User
from app.domain.users.repositories import UserRepository
from app.infrastructure.database.models.user import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(model)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if self._is_unique_email_violation(exc):
                raise UserEmailAlreadyExistsError(
                    f"User email '{user.email}' already exists."
                ) from exc
            raise

        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            password_hash=model.password_hash,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _is_unique_email_violation(exc: IntegrityError) -> bool:
        original_error = getattr(exc, "orig", None)
        return (
            getattr(original_error, "sqlstate", None) == "23505"
            and getattr(original_error, "constraint_name", None) == "uq_users_email"
        )
