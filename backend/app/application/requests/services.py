from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.request_activities.schemas import RequestActivityReadModel
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipNotFoundError,
)
from app.application.organizations.exceptions import OrganizationNotFoundError
from app.application.requests.commands import CreateRequestCommand
from app.application.requests.commands import TransitionRequestStatusCommand
from app.application.requests.exceptions import (
    InvalidRequestStatusTransitionError,
    RequestMembershipOrganizationMismatchError,
    RequestNotFoundError,
    RequestOrganizationMismatchError,
)
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.application.requests.schemas import RequestReadModel
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.requests.entities import Request
from app.domain.requests.repositories import RequestRepository
from app.domain.requests.statuses import RequestStatus
from app.domain.requests.transitions import is_valid_request_status_transition


class CreateRequestUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_activity_repository: RequestActivityRepository,
        organization_repository: OrganizationRepository,
        organization_membership_repository: OrganizationMembershipRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_activity_repository = request_activity_repository
        self._organization_repository = organization_repository
        self._organization_membership_repository = organization_membership_repository

    async def execute(self, command: CreateRequestCommand) -> RequestReadModel:
        organization = await self._organization_repository.get_by_id(command.organization_id)
        if organization is None:
            raise OrganizationNotFoundError(
                f"Organization '{command.organization_id}' was not found."
            )

        membership = await self._organization_membership_repository.get_by_id(
            command.created_by_membership_id
        )
        if membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{command.created_by_membership_id}' was not found."
            )

        if membership.organization_id != command.organization_id:
            raise RequestMembershipOrganizationMismatchError(
                "The provided membership does not belong to the provided organization."
            )

        now = datetime.now(UTC)
        request = Request(
            id=uuid4(),
            organization_id=command.organization_id,
            title=command.title,
            description=command.description,
            status=RequestStatus.NEW,
            source=command.source,
            created_by_membership_id=command.created_by_membership_id,
            created_at=now,
            updated_at=now,
        )
        created_request = await self._request_repository.add(request)
        await self._request_activity_repository.add(
            RequestActivity(
                id=uuid4(),
                request_id=created_request.id,
                organization_id=created_request.organization_id,
                membership_id=created_request.created_by_membership_id,
                type=RequestActivityType.REQUEST_CREATED,
                payload={
                    "request_id": str(created_request.id),
                    "status": created_request.status.value,
                    "source": created_request.source.value,
                    "title": created_request.title,
                },
                created_at=now,
            )
        )
        await self._request_repository.save_changes()
        return RequestReadModel.model_validate(created_request, from_attributes=True)


class GetRequestByIdUseCase:
    def __init__(self, request_repository: RequestRepository) -> None:
        self._request_repository = request_repository

    async def execute(self, request_id: UUID, organization_id: UUID) -> RequestReadModel:
        request = await self._request_repository.get_by_id(request_id)
        if request is None or request.organization_id != organization_id:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        return RequestReadModel.model_validate(request, from_attributes=True)


class ListRequestsUseCase:
    def __init__(self, request_repository: RequestRepository) -> None:
        self._request_repository = request_repository

    async def execute(self, organization_id: UUID) -> list[RequestReadModel]:
        requests = await self._request_repository.list_by_organization_id(organization_id)
        return [
            RequestReadModel.model_validate(request, from_attributes=True)
            for request in requests
        ]


class TransitionRequestStatusUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_activity_repository: RequestActivityRepository,
        organization_membership_repository: OrganizationMembershipRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_activity_repository = request_activity_repository
        self._organization_membership_repository = organization_membership_repository

    async def execute(
        self,
        request_id: UUID,
        command: TransitionRequestStatusCommand,
    ) -> RequestReadModel:
        request = await self._request_repository.get_by_id(request_id)
        if request is None:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        if request.organization_id != command.organization_id:
            raise RequestOrganizationMismatchError(
                "The provided request does not belong to the provided organization."
            )

        membership = await self._organization_membership_repository.get_by_id(
            command.membership_id
        )
        if membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{command.membership_id}' was not found."
            )

        if membership.organization_id != command.organization_id:
            raise RequestMembershipOrganizationMismatchError(
                "The provided membership does not belong to the provided organization."
            )

        if not is_valid_request_status_transition(request.status, command.new_status):
            raise InvalidRequestStatusTransitionError(
                f"Cannot transition request from '{request.status.value}' to '{command.new_status.value}'."
            )

        now = datetime.now(UTC)
        updated_request = await self._request_repository.update_status(
            request_id=request.id,
            new_status=command.new_status,
            updated_at=now,
        )
        await self._request_activity_repository.add(
            RequestActivity(
                id=uuid4(),
                request_id=updated_request.id,
                organization_id=updated_request.organization_id,
                membership_id=command.membership_id,
                type=RequestActivityType.STATUS_CHANGED,
                payload={
                    "request_id": str(updated_request.id),
                    "old_status": request.status.value,
                    "new_status": command.new_status.value,
                },
                created_at=now,
            )
        )
        await self._request_repository.save_changes()
        return RequestReadModel.model_validate(updated_request, from_attributes=True)


class ListRequestActivitiesUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_activity_repository: RequestActivityRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_activity_repository = request_activity_repository

    async def execute(
        self,
        request_id: UUID,
        organization_id: UUID,
    ) -> list[RequestActivityReadModel]:
        request = await self._request_repository.get_by_id(request_id)
        if request is None or request.organization_id != organization_id:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        activities = await self._request_activity_repository.list_by_request_id(request_id)
        return [
            RequestActivityReadModel.model_validate(activity, from_attributes=True)
            for activity in activities
        ]
