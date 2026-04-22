from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.customers.entities import Customer
from app.domain.customers.repositories import CustomerRepository
from app.infrastructure.database.models.customer import CustomerModel


class SqlAlchemyCustomerRepository(CustomerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, customer: Customer) -> Customer:
        model = CustomerModel(
            id=customer.id,
            organization_id=customer.organization_id,
            name=customer.name,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )
        self._session.add(model)
        return customer

    async def get_by_id_and_organization(
        self,
        customer_id: UUID,
        organization_id: UUID,
    ) -> Customer | None:
        statement = select(CustomerModel).where(
            CustomerModel.id == customer_id,
            CustomerModel.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_ids_and_organization(
        self,
        customer_ids: list[UUID],
        organization_id: UUID,
    ) -> list[Customer]:
        if not customer_ids:
            return []

        statement = select(CustomerModel).where(
            CustomerModel.organization_id == organization_id,
            CustomerModel.id.in_(customer_ids),
        )
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(model: CustomerModel) -> Customer:
        return Customer(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
