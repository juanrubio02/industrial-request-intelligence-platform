from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.organization_memberships.entities import OrganizationMembership


class OrganizationMembershipRepository(ABC):
    @abstractmethod
    async def add(self, membership: OrganizationMembership) -> OrganizationMembership:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, membership_id: UUID) -> OrganizationMembership | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_and_organization(
        self,
        membership_id: UUID,
        organization_id: UUID,
    ) -> OrganizationMembership | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_user_and_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> OrganizationMembership | None:
        raise NotImplementedError

    @abstractmethod
    async def list_active_by_user_id(
        self,
        user_id: UUID,
    ) -> list[OrganizationMembership]:
        raise NotImplementedError
