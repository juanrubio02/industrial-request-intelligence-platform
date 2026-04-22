from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.customers.entities import Customer


class CustomerRepository(ABC):
    @abstractmethod
    async def add(self, customer: Customer) -> Customer:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_and_organization(
        self,
        customer_id: UUID,
        organization_id: UUID,
    ) -> Customer | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_ids_and_organization(
        self,
        customer_ids: list[UUID],
        organization_id: UUID,
    ) -> list[Customer]:
        raise NotImplementedError
