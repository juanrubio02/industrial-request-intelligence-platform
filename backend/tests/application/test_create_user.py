import pytest

from app.infrastructure.auth.password import ScryptPasswordHasher
from app.application.users.commands import CreateUserCommand
from app.application.users.exceptions import UserEmailAlreadyExistsError
from app.application.users.services import CreateUserUseCase
from app.domain.users.entities import User
from app.domain.users.repositories import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users_by_email: dict[str, User] = {}
        self._users_by_id: dict[object, User] = {}

    async def add(self, user: User) -> User:
        self._users_by_email[user.email] = user
        self._users_by_id[user.id] = user
        return user

    async def get_by_id(self, user_id):
        return self._users_by_id.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email)


@pytest.mark.anyio
async def test_create_user_use_case_creates_active_user() -> None:
    repository = InMemoryUserRepository()
    use_case = CreateUserUseCase(
        user_repository=repository,
        password_hasher=ScryptPasswordHasher(),
    )

    result = await use_case.execute(
        CreateUserCommand(
            email="alice@example.com",
            full_name="Alice Example",
            password="StrongPass123!",
        )
    )

    assert result.email == "alice@example.com"
    assert result.full_name == "Alice Example"
    assert result.is_active is True
    stored_user = await repository.get_by_email("alice@example.com")
    assert stored_user is not None
    assert stored_user.password_hash is not None


@pytest.mark.anyio
async def test_create_user_use_case_rejects_duplicate_email() -> None:
    repository = InMemoryUserRepository()
    use_case = CreateUserUseCase(
        user_repository=repository,
        password_hasher=ScryptPasswordHasher(),
    )
    await use_case.execute(
        CreateUserCommand(
            email="alice@example.com",
            full_name="Alice Example",
            password="StrongPass123!",
        )
    )

    with pytest.raises(UserEmailAlreadyExistsError):
        await use_case.execute(
            CreateUserCommand(
                email="alice@example.com",
                full_name="Another Alice",
                password="AnotherPass123!",
            )
        )
