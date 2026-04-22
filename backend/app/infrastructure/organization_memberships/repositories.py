from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.organization_memberships.exceptions import (
    OrganizationMembershipAlreadyExistsError,
)
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus
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
            status=membership.status,
            is_active=membership.is_active,
            joined_at=membership.joined_at,
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

        return membership

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
        *,
        limit: int | None = None,
        offset: int = 0,
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
        if offset:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def count_active_by_user_id(
        self,
        user_id: UUID,
    ) -> int:
        statement = select(func.count(OrganizationMembershipModel.id)).where(
            OrganizationMembershipModel.user_id == user_id,
            OrganizationMembershipModel.is_active.is_(True),
        )
        result = await self._session.execute(statement)
        return int(result.scalar() or 0)

    async def list_active_by_organization_id(
        self,
        organization_id: UUID,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[OrganizationMembership]:
        statement = (
            select(OrganizationMembershipModel)
            .where(
                OrganizationMembershipModel.organization_id == organization_id,
                OrganizationMembershipModel.is_active.is_(True),
            )
            .order_by(
                OrganizationMembershipModel.created_at.asc(),
                OrganizationMembershipModel.id.asc(),
            )
        )
        if offset:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_by_organization_id(
        self,
        organization_id: UUID,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[OrganizationMembership]:
        statement = (
            select(OrganizationMembershipModel)
            .where(OrganizationMembershipModel.organization_id == organization_id)
            .order_by(
                OrganizationMembershipModel.created_at.asc(),
                OrganizationMembershipModel.id.asc(),
            )
        )
        if offset:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._session.execute(statement)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def count_by_organization_id(
        self,
        organization_id: UUID,
    ) -> int:
        statement = select(func.count(OrganizationMembershipModel.id)).where(
            OrganizationMembershipModel.organization_id == organization_id
        )
        result = await self._session.execute(statement)
        return int(result.scalar() or 0)

    async def list_by_ids_and_organization(
        self,
        membership_ids: Sequence[UUID],
        organization_id: UUID,
    ) -> list[OrganizationMembership]:
        if not membership_ids:
            return []

        statement = select(OrganizationMembershipModel).where(
            OrganizationMembershipModel.id.in_(membership_ids),
            OrganizationMembershipModel.organization_id == organization_id,
        )
        result = await self._session.execute(statement)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def save(self, membership: OrganizationMembership) -> OrganizationMembership:
        model = await self._session.get(OrganizationMembershipModel, membership.id)
        if model is None:
            raise ValueError(f"Membership '{membership.id}' was not found.")

        model.role = membership.role
        model.status = membership.status
        model.is_active = membership.is_active
        model.joined_at = membership.joined_at
        model.updated_at = membership.updated_at

        await self._session.commit()
        return membership

    async def count_active_by_organization_and_role(
        self,
        organization_id: UUID,
        role: OrganizationMembershipRole,
    ) -> int:
        statement = select(func.count(OrganizationMembershipModel.id)).where(
            OrganizationMembershipModel.organization_id == organization_id,
            OrganizationMembershipModel.role == role,
            OrganizationMembershipModel.status == OrganizationMembershipStatus.ACTIVE,
        )
        result = await self._session.execute(statement)
        return int(result.scalar() or 0)

    @staticmethod
    def _to_domain(model: OrganizationMembershipModel) -> OrganizationMembership:
        return OrganizationMembership(
            id=model.id,
            organization_id=model.organization_id,
            user_id=model.user_id,
            role=model.role,
            status=model.status,
            joined_at=model.joined_at,
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
