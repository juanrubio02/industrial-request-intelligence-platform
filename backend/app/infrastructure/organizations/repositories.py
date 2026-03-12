from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.organizations.exceptions import OrganizationSlugAlreadyExistsError
from app.domain.organizations.entities import Organization
from app.domain.organizations.repositories import OrganizationRepository
from app.infrastructure.database.models.organization import OrganizationModel


class SqlAlchemyOrganizationRepository(OrganizationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, organization: Organization) -> Organization:
        model = OrganizationModel(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            is_active=organization.is_active,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
        )
        self._session.add(model)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise OrganizationSlugAlreadyExistsError(
                f"Organization slug '{organization.slug}' already exists."
            ) from exc

        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        model = await self._session.get(OrganizationModel, organization_id)
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_slug(self, slug: str) -> Organization | None:
        statement = select(OrganizationModel).where(OrganizationModel.slug == slug)
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: OrganizationModel) -> Organization:
        return Organization(
            id=model.id,
            name=model.name,
            slug=model.slug,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
