from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.organizations.commands import CreateOrganizationCommand
from app.application.organizations.schemas import OrganizationReadModel
from app.application.organizations.services import (
    CreateOrganizationUseCase,
    GetOrganizationByIdUseCase,
)
from app.infrastructure.database.session import get_db_session
from app.infrastructure.organizations.repositories import SqlAlchemyOrganizationRepository
from app.interfaces.http.schemas.organizations import CreateOrganizationRequest

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationReadModel, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: CreateOrganizationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationReadModel:
    repository = SqlAlchemyOrganizationRepository(session=session)
    use_case = CreateOrganizationUseCase(organization_repository=repository)
    command = CreateOrganizationCommand(name=payload.name, slug=payload.slug)
    return await use_case.execute(command)


@router.get("/{organization_id}", response_model=OrganizationReadModel)
async def get_organization(
    organization_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationReadModel:
    repository = SqlAlchemyOrganizationRepository(session=session)
    use_case = GetOrganizationByIdUseCase(organization_repository=repository)
    return await use_case.execute(organization_id)

