from datetime import UTC, datetime
from uuid import uuid4

from app.application.auth.password import PasswordHasher
from app.application.users.commands import CreateUserCommand
from app.application.users.exceptions import UserEmailAlreadyExistsError
from app.application.users.schemas import UserReadModel
from app.domain.users.entities import User
from app.domain.users.repositories import UserRepository


class CreateUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    async def execute(self, command: CreateUserCommand) -> UserReadModel:
        existing_user = await self._user_repository.get_by_email(command.email)
        if existing_user is not None:
            raise UserEmailAlreadyExistsError(f"User email '{command.email}' already exists.")

        now = datetime.now(UTC)
        user = User(
            id=uuid4(),
            email=command.email,
            full_name=command.full_name,
            password_hash=self._password_hasher.hash(command.password),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        created_user = await self._user_repository.add(user)
        return UserReadModel.model_validate(created_user, from_attributes=True)
