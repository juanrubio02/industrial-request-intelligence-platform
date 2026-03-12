from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.organization_memberships.commands import CreateOrganizationMembershipCommand
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipAlreadyExistsError,
    OrganizationMembershipNotFoundError,
)
from app.application.organization_memberships.schemas import OrganizationMembershipReadModel
from app.application.organizations.exceptions import OrganizationNotFoundError
from app.application.users.exceptions import UserNotFoundError
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.users.repositories import UserRepository


class CreateOrganizationMembershipUseCase:
    def __init__(
        self,
        organization_membership_repository: OrganizationMembershipRepository,
        organization_repository: OrganizationRepository,
        user_repository: UserRepository,
    ) -> None:
        self._organization_membership_repository = organization_membership_repository
        self._organization_repository = organization_repository
        self._user_repository = user_repository

    async def execute(
        self,
        command: CreateOrganizationMembershipCommand,
    ) -> OrganizationMembershipReadModel:
        organization = await self._organization_repository.get_by_id(command.organization_id)
        if organization is None:
            raise OrganizationNotFoundError(
                f"Organization '{command.organization_id}' was not found."
            )

        user = await self._user_repository.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(f"User '{command.user_id}' was not found.")

        existing_membership = await self._organization_membership_repository.get_active_by_user_and_organization(
            user_id=command.user_id,
            organization_id=command.organization_id,
        )
        if existing_membership is not None:
            raise OrganizationMembershipAlreadyExistsError(
                "An active membership already exists for this user in the organization."
            )

        now = datetime.now(UTC)
        membership = OrganizationMembership(
            id=uuid4(),
            organization_id=command.organization_id,
            user_id=command.user_id,
            role=command.role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        created_membership = await self._organization_membership_repository.add(membership)
        return OrganizationMembershipReadModel.model_validate(
            created_membership,
            from_attributes=True,
        )


class GetOrganizationMembershipUseCase:
    def __init__(
        self,
        organization_membership_repository: OrganizationMembershipRepository,
    ) -> None:
        self._organization_membership_repository = organization_membership_repository

    async def execute(
        self,
        organization_id: UUID,
        membership_id: UUID,
    ) -> OrganizationMembershipReadModel:
        membership = await self._organization_membership_repository.get_by_id_and_organization(
            membership_id=membership_id,
            organization_id=organization_id,
        )
        if membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{membership_id}' was not found in organization '{organization_id}'."
            )

        return OrganizationMembershipReadModel.model_validate(membership, from_attributes=True)
