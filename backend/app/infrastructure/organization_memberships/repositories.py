from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.organization_memberships.exceptions import (
    OrganizationMembershipAlreadyExistsError,
)
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.infrastructure.database.models.organization_membership import OrganizationMembershipModel


class SqlAlchemyOrganizationMembershipRepository(OrganizationMembershipRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, membership: OrganizationMembership) -> OrganizationMembership:
        model = OrganizationMembershipModel(
            id=membership.id,
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            role=membership.role,
            is_active=membership.is_active,
            created_at=membership.created_at,
            updated_at=membership.updated_at,
        )
        self._session.add(model)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if self._is_duplicate_active_membership_violation(exc):
                raise OrganizationMembershipAlreadyExistsError(
                    "An active membership already exists for this user in the organization."
                ) from exc
            raise

        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, membership_id: UUID) -> OrganizationMembership | None:
        model = await self._session.get(OrganizationMembershipModel, membership_id)
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_id_and_organization(
        self,
        membership_id: UUID,
        organization_id: UUID,
    ) -> OrganizationMembership | None:
        statement = select(OrganizationMembershipModel).where(
            OrganizationMembershipModel.id == membership_id,
            OrganizationMembershipModel.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_active_by_user_and_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> OrganizationMembership | None:
        statement = select(OrganizationMembershipModel).where(
            OrganizationMembershipModel.user_id == user_id,
            OrganizationMembershipModel.organization_id == organization_id,
            OrganizationMembershipModel.is_active.is_(True),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_active_by_user_id(
        self,
        user_id: UUID,
    ) -> list[OrganizationMembership]:
        statement = (
            select(OrganizationMembershipModel)
            .where(
                OrganizationMembershipModel.user_id == user_id,
                OrganizationMembershipModel.is_active.is_(True),
            )
            .order_by(
                OrganizationMembershipModel.created_at.asc(),
                OrganizationMembershipModel.id.asc(),
            )
        )
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(model: OrganizationMembershipModel) -> OrganizationMembership:
        return OrganizationMembership(
            id=model.id,
            organization_id=model.organization_id,
            user_id=model.user_id,
            role=model.role,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _is_duplicate_active_membership_violation(exc: IntegrityError) -> bool:
        original_error = getattr(exc, "orig", None)
        return (
            getattr(original_error, "sqlstate", None) == "23505"
            and getattr(original_error, "constraint_name", None)
            == "ix_organization_memberships_active_org_user_unique"
        )
