from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.organizations.commands import CreateOrganizationCommand
from app.application.organizations.exceptions import OrganizationSlugAlreadyExistsError
from app.application.organizations.services import CreateOrganizationUseCase
from app.domain.organizations.entities import Organization
from app.domain.organizations.repositories import OrganizationRepository


class InMemoryOrganizationRepository(OrganizationRepository):
    def __init__(self) -> None:
        self.organizations: dict[str, Organization] = {}

    async def add(self, organization: Organization) -> Organization:
        self.organizations[organization.slug] = organization
        return organization

    async def get_by_id(self, organization_id):
        for organization in self.organizations.values():
            if organization.id == organization_id:
                return organization
        return None

    async def get_by_slug(self, slug: str) -> Organization | None:
        return self.organizations.get(slug)


@pytest.mark.anyio
async def test_create_organization_use_case_creates_active_organization() -> None:
    repository = InMemoryOrganizationRepository()
    use_case = CreateOrganizationUseCase(organization_repository=repository)

    result = await use_case.execute(
        CreateOrganizationCommand(name="Acme Industrial", slug="acme-industrial")
    )

    assert result.name == "Acme Industrial"
    assert result.slug == "acme-industrial"
    assert result.is_active is True


@pytest.mark.anyio
async def test_create_organization_use_case_rejects_duplicate_slug() -> None:
    existing = Organization(
        id=uuid4(),
        name="Existing",
        slug="existing-org",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository = InMemoryOrganizationRepository()
    repository.organizations[existing.slug] = existing
    use_case = CreateOrganizationUseCase(organization_repository=repository)

    with pytest.raises(OrganizationSlugAlreadyExistsError):
        await use_case.execute(CreateOrganizationCommand(name="Another", slug="existing-org"))

