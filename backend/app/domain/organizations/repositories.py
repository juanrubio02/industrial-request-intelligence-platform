from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.organizations.entities import Organization


class OrganizationRepository(ABC):
    @abstractmethod
    async def add(self, organization: Organization) -> Organization:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Organization | None:
        raise NotImplementedError

