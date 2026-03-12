from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.organizations.commands import CreateOrganizationCommand
from app.application.organizations.exceptions import (
    OrganizationNotFoundError,
    OrganizationSlugAlreadyExistsError,
)
from app.application.organizations.schemas import OrganizationReadModel
from app.domain.organizations.entities import Organization
from app.domain.organizations.repositories import OrganizationRepository


class CreateOrganizationUseCase:
    def __init__(self, organization_repository: OrganizationRepository) -> None:
        self._organization_repository = organization_repository

    async def execute(self, command: CreateOrganizationCommand) -> OrganizationReadModel:
        existing_organization = await self._organization_repository.get_by_slug(command.slug)
        if existing_organization is not None:
            raise OrganizationSlugAlreadyExistsError(
                f"Organization slug '{command.slug}' already exists."
            )

        now = datetime.now(UTC)
        organization = Organization(
            id=uuid4(),
            name=command.name,
            slug=command.slug,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        created_organization = await self._organization_repository.add(organization)
        return OrganizationReadModel.model_validate(created_organization, from_attributes=True)


class GetOrganizationByIdUseCase:
    def __init__(self, organization_repository: OrganizationRepository) -> None:
        self._organization_repository = organization_repository

    async def execute(self, organization_id: UUID) -> OrganizationReadModel:
        organization = await self._organization_repository.get_by_id(organization_id)
        if organization is None:
            raise OrganizationNotFoundError(f"Organization '{organization_id}' was not found.")

        return OrganizationReadModel.model_validate(organization, from_attributes=True)

