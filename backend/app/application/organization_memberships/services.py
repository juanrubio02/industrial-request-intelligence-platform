from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.auth.authorization import MembershipAuthorizationService
from app.application.common.pagination import PaginatedResult, PaginationParams
from app.application.organization_memberships.commands import CreateOrganizationMembershipCommand
from app.application.organization_memberships.commands import (
    UpdateOrganizationMembershipRoleCommand,
    UpdateOrganizationMembershipStatusCommand,
)
from app.application.organization_memberships.exceptions import (
    LastOrganizationOwnerChangeError,
    OrganizationMembershipAlreadyExistsError,
    OrganizationMembershipNotFoundError,
    OrganizationMembershipRoleUpdateNotAllowedError,
    OrganizationMembershipStatusUpdateNotAllowedError,
)
from app.application.organization_memberships.schemas import (
    OrganizationMembershipOptionReadModel,
    OrganizationMembershipReadModel,
)
from app.application.organizations.exceptions import OrganizationNotFoundError
from app.application.users.exceptions import UserNotFoundError
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus
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
            status=OrganizationMembershipStatus.ACTIVE,
            joined_at=now,
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


class ListOrganizationMembershipsUseCase:
    def __init__(
        self,
        organization_membership_repository: OrganizationMembershipRepository,
        user_repository: UserRepository,
    ) -> None:
        self._organization_membership_repository = organization_membership_repository
        self._user_repository = user_repository

    async def execute(
        self,
        organization_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResult[OrganizationMembershipOptionReadModel]:
        memberships = await self._organization_membership_repository.list_by_organization_id(
            organization_id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        total = await self._organization_membership_repository.count_by_organization_id(
            organization_id
        )
        users_by_id = {
            user.id: user
            for user in await self._user_repository.list_by_ids(
                [membership.user_id for membership in memberships]
            )
        }
        items: list[OrganizationMembershipOptionReadModel] = []
        for membership in memberships:
            user = users_by_id.get(membership.user_id)
            if user is None:
                continue

            items.append(
                OrganizationMembershipOptionReadModel(
                    id=membership.id,
                    organization_id=membership.organization_id,
                    user_id=membership.user_id,
                    user_full_name=user.full_name,
                    user_email=user.email,
                    role=membership.role,
                    status=membership.status,
                    joined_at=membership.joined_at,
                    created_at=membership.created_at,
                    updated_at=membership.updated_at,
                )
            )
        return PaginatedResult(
            items=items,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )


class UpdateOrganizationMembershipRoleUseCase:
    def __init__(
        self,
        organization_membership_repository: OrganizationMembershipRepository,
        authorization_service: MembershipAuthorizationService,
    ) -> None:
        self._organization_membership_repository = organization_membership_repository
        self._authorization_service = authorization_service

    async def execute(
        self,
        membership_id: UUID,
        command: UpdateOrganizationMembershipRoleCommand,
    ) -> OrganizationMembershipReadModel:
        actor_membership = await self._organization_membership_repository.get_by_id(
            command.actor_membership_id
        )
        target_membership = (
            await self._organization_membership_repository.get_by_id_and_organization(
                membership_id=membership_id,
                organization_id=command.organization_id,
            )
        )
        if actor_membership is None or target_membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{membership_id}' was not found in organization '{command.organization_id}'."
            )

        if actor_membership.organization_id != command.organization_id:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{membership_id}' was not found in organization '{command.organization_id}'."
            )

        if not self._authorization_service.can_manage_members(
            actor_membership=OrganizationMembershipReadModel.model_validate(
                actor_membership,
                from_attributes=True,
            )
        ):
            raise OrganizationMembershipRoleUpdateNotAllowedError(
                "The current membership cannot update member roles."
            )

        actor_read_model = OrganizationMembershipReadModel.model_validate(
            actor_membership,
            from_attributes=True,
        )
        target_read_model = OrganizationMembershipReadModel.model_validate(
            target_membership,
            from_attributes=True,
        )

        if not self._authorization_service.can_manage_target_membership(
            actor_membership=actor_read_model,
            target_membership=target_read_model,
        ) or not self._authorization_service.can_assign_role(
            actor_membership=actor_read_model,
            role=command.role,
        ):
            raise OrganizationMembershipRoleUpdateNotAllowedError(
                "The current membership cannot assign this role."
            )

        if (
            target_membership.role == OrganizationMembershipRole.OWNER
            and command.role != OrganizationMembershipRole.OWNER
            and target_membership.status == OrganizationMembershipStatus.ACTIVE
        ):
            owners_count = (
                await self._organization_membership_repository.count_active_by_organization_and_role(
                    command.organization_id,
                    OrganizationMembershipRole.OWNER,
                )
            )
            if owners_count <= 1:
                raise LastOrganizationOwnerChangeError(
                    "The last active owner cannot lose the OWNER role."
                )

        updated_membership = OrganizationMembership(
            id=target_membership.id,
            organization_id=target_membership.organization_id,
            user_id=target_membership.user_id,
            role=command.role,
            status=target_membership.status,
            joined_at=target_membership.joined_at,
            created_at=target_membership.created_at,
            updated_at=datetime.now(UTC),
        )
        saved_membership = await self._organization_membership_repository.save(
            updated_membership
        )
        return OrganizationMembershipReadModel.model_validate(
            saved_membership,
            from_attributes=True,
        )


class UpdateOrganizationMembershipStatusUseCase:
    def __init__(
        self,
        organization_membership_repository: OrganizationMembershipRepository,
        authorization_service: MembershipAuthorizationService,
    ) -> None:
        self._organization_membership_repository = organization_membership_repository
        self._authorization_service = authorization_service

    async def execute(
        self,
        membership_id: UUID,
        command: UpdateOrganizationMembershipStatusCommand,
    ) -> OrganizationMembershipReadModel:
        actor_membership = await self._organization_membership_repository.get_by_id(
            command.actor_membership_id
        )
        target_membership = (
            await self._organization_membership_repository.get_by_id_and_organization(
                membership_id=membership_id,
                organization_id=command.organization_id,
            )
        )
        if actor_membership is None or target_membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{membership_id}' was not found in organization '{command.organization_id}'."
            )

        if actor_membership.organization_id != command.organization_id:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{membership_id}' was not found in organization '{command.organization_id}'."
            )

        actor_read_model = OrganizationMembershipReadModel.model_validate(
            actor_membership,
            from_attributes=True,
        )
        target_read_model = OrganizationMembershipReadModel.model_validate(
            target_membership,
            from_attributes=True,
        )

        if not self._authorization_service.can_manage_target_membership(
            actor_membership=actor_read_model,
            target_membership=target_read_model,
        ):
            raise OrganizationMembershipStatusUpdateNotAllowedError(
                "The current membership cannot update this member status."
            )

        if (
            target_membership.role == OrganizationMembershipRole.OWNER
            and target_membership.status == OrganizationMembershipStatus.ACTIVE
            and command.status == OrganizationMembershipStatus.DISABLED
        ):
            owners_count = (
                await self._organization_membership_repository.count_active_by_organization_and_role(
                    command.organization_id,
                    OrganizationMembershipRole.OWNER,
                )
            )
            if owners_count <= 1:
                raise LastOrganizationOwnerChangeError(
                    "The last active owner cannot be disabled."
                )

        updated_membership = OrganizationMembership(
            id=target_membership.id,
            organization_id=target_membership.organization_id,
            user_id=target_membership.user_id,
            role=target_membership.role,
            status=command.status,
            joined_at=target_membership.joined_at,
            created_at=target_membership.created_at,
            updated_at=datetime.now(UTC),
        )
        saved_membership = await self._organization_membership_repository.save(
            updated_membership
        )
        return OrganizationMembershipReadModel.model_validate(
            saved_membership,
            from_attributes=True,
        )
