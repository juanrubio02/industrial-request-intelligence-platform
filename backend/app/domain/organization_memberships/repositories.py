from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.roles import OrganizationMembershipRole


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
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[OrganizationMembership]:
        raise NotImplementedError

    @abstractmethod
    async def count_active_by_user_id(
        self,
        user_id: UUID,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def list_active_by_organization_id(
        self,
        organization_id: UUID,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[OrganizationMembership]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_organization_id(
        self,
        organization_id: UUID,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[OrganizationMembership]:
        raise NotImplementedError

    @abstractmethod
    async def count_by_organization_id(
        self,
        organization_id: UUID,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def list_by_ids_and_organization(
        self,
        membership_ids: Sequence[UUID],
        organization_id: UUID,
    ) -> list[OrganizationMembership]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, membership: OrganizationMembership) -> OrganizationMembership:
        raise NotImplementedError

    @abstractmethod
    async def count_active_by_organization_and_role(
        self,
        organization_id: UUID,
        role: OrganizationMembershipRole,
    ) -> int:
        raise NotImplementedError
