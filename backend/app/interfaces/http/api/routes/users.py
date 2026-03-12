from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.users.commands import CreateUserCommand
from app.application.users.schemas import UserReadModel
from app.application.users.services import CreateUserUseCase
from app.infrastructure.database.session import get_db_session
from app.interfaces.http.dependencies import get_password_hasher
from app.application.auth.password import PasswordHasher
from app.infrastructure.users.repositories import SqlAlchemyUserRepository
from app.interfaces.http.schemas.users import CreateUserRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserReadModel, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    session: AsyncSession = Depends(get_db_session),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> UserReadModel:
    repository = SqlAlchemyUserRepository(session=session)
    use_case = CreateUserUseCase(user_repository=repository, password_hasher=password_hasher)
    command = CreateUserCommand(
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
    )
    return await use_case.execute(command)
