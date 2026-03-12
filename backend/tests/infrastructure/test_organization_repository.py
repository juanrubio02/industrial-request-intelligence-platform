import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.organizations.commands import CreateOrganizationCommand
from app.application.organizations.services import CreateOrganizationUseCase
from app.infrastructure.organizations.repositories import SqlAlchemyOrganizationRepository


@pytest.mark.anyio
async def test_repository_persists_and_reads_organization(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repository = SqlAlchemyOrganizationRepository(session=session)
        use_case = CreateOrganizationUseCase(organization_repository=repository)
        created = await use_case.execute(
            CreateOrganizationCommand(name="Factory Corp", slug="factory-corp")
        )

    async with session_factory() as session:
        repository = SqlAlchemyOrganizationRepository(session=session)
        organization = await repository.get_by_id(created.id)

    assert organization is not None
    assert organization.name == "Factory Corp"
    assert organization.slug == "factory-corp"
