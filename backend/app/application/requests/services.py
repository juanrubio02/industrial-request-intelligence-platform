from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.pagination import PaginatedResult, PaginationParams
from app.domain.customers.entities import Customer
from app.domain.customers.repositories import CustomerRepository
from app.application.common.exceptions import ValidationError
from app.application.request_activities.schemas import RequestActivityReadModel
from app.application.request_activities.schemas import RequestActivityActorReadModel
from app.application.requests.commands import AssignRequestCommand
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipNotFoundError,
)
from app.application.organizations.exceptions import OrganizationNotFoundError
from app.application.requests.commands import CreateRequestCommand
from app.application.requests.commands import ListRequestsFilters
from app.application.requests.commands import TransitionRequestStatusCommand
from app.application.requests.commands import UpdateRequestCommand
from app.application.requests.exceptions import (
    InvalidRequestStatusTransitionError,
    RequestAssignedMembershipOrganizationMismatchError,
    RequestCustomerNotFoundError,
    RequestMembershipOrganizationMismatchError,
    RequestNotFoundError,
)
from app.application.requests.schemas import RequestReadModel
from app.application.requests.schemas import RequestCustomerSummaryReadModel
from app.domain.documents.repositories import DocumentRepository
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.domain.request_comments.repositories import RequestCommentRepository
from app.domain.request_status_history.entities import RequestStatusHistoryEntry
from app.domain.request_status_history.repositories import RequestStatusHistoryRepository
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organizations.repositories import OrganizationRepository
from app.domain.requests.entities import Request
from app.domain.requests.repositories import RequestRepository
from app.domain.requests.statuses import RequestStatus
from app.domain.requests.transitions import (
    get_available_request_status_transitions,
    is_valid_request_status_transition,
)


def _to_request_read_model(
    request: Request,
    *,
    customer: RequestCustomerSummaryReadModel | None = None,
    documents_count: int = 0,
    comments_count: int = 0,
) -> RequestReadModel:
    return RequestReadModel(
        id=request.id,
        organization_id=request.organization_id,
        customer_id=request.customer_id,
        customer=customer,
        title=request.title,
        description=request.description,
        status=request.status,
        source=request.source,
        created_by_membership_id=request.created_by_membership_id,
        assigned_membership_id=request.assigned_membership_id,
        documents_count=documents_count,
        comments_count=comments_count,
        available_status_transitions=get_available_request_status_transitions(request.status),
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def _to_customer_summary_read_model(
    customer: Customer,
) -> RequestCustomerSummaryReadModel:
    return RequestCustomerSummaryReadModel(
        id=customer.id,
        name=customer.name,
    )


def _to_request_activity_read_model(
    activity: RequestActivity,
    *,
    actor_user_id: UUID | None,
) -> RequestActivityReadModel:
    return RequestActivityReadModel(
        id=activity.id,
        request_id=activity.request_id,
        organization_id=activity.organization_id,
        membership_id=activity.membership_id,
        actor=RequestActivityActorReadModel(
            membership_id=activity.membership_id,
            user_id=actor_user_id,
        ),
        type=activity.type,
        payload=activity.payload,
        metadata=activity.payload,
        created_at=activity.created_at,
    )


class CreateRequestUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_activity_repository: RequestActivityRepository,
        request_status_history_repository: RequestStatusHistoryRepository,
        organization_repository: OrganizationRepository,
        organization_membership_repository: OrganizationMembershipRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_activity_repository = request_activity_repository
        self._request_status_history_repository = request_status_history_repository
        self._organization_repository = organization_repository
        self._organization_membership_repository = organization_membership_repository
        self._customer_repository = customer_repository

    async def execute(
        self,
        organization_id: UUID,
        command: CreateRequestCommand,
    ) -> RequestReadModel:
        organization = await self._organization_repository.get_by_id(organization_id)
        if organization is None:
            raise OrganizationNotFoundError(
                f"Organization '{organization_id}' was not found."
            )

        membership = await self._organization_membership_repository.get_by_id(
            command.created_by_membership_id
        )
        if membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{command.created_by_membership_id}' was not found."
            )

        if membership.organization_id != organization_id:
            raise RequestMembershipOrganizationMismatchError(
                "The provided membership does not belong to the provided organization."
            )

        customer_summary: RequestCustomerSummaryReadModel | None = None
        if command.customer_id is not None:
            customer = await self._customer_repository.get_by_id_and_organization(
                command.customer_id,
                organization_id,
            )
            if customer is None:
                raise RequestCustomerNotFoundError(
                    f"Customer '{command.customer_id}' was not found."
                )
            customer_summary = _to_customer_summary_read_model(customer)

        now = datetime.now(UTC)
        request = Request(
            id=uuid4(),
            organization_id=organization_id,
            title=command.title,
            description=command.description,
            status=RequestStatus.NEW,
            source=command.source,
            created_by_membership_id=command.created_by_membership_id,
            assigned_membership_id=None,
            created_at=now,
            updated_at=now,
            customer_id=command.customer_id,
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
        await self._request_status_history_repository.add(
            RequestStatusHistoryEntry(
                id=uuid4(),
                request_id=created_request.id,
                organization_id=created_request.organization_id,
                previous_status=None,
                new_status=created_request.status,
                changed_at=now,
                changed_by=created_request.created_by_membership_id,
                changed_by_user_id=membership.user_id,
            )
        )
        await self._request_repository.save_changes()
        return _to_request_read_model(created_request, customer=customer_summary)


class GetRequestByIdUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        document_repository: DocumentRepository,
        request_comment_repository: RequestCommentRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._request_repository = request_repository
        self._document_repository = document_repository
        self._request_comment_repository = request_comment_repository
        self._customer_repository = customer_repository

    async def execute(self, request_id: UUID, organization_id: UUID) -> RequestReadModel:
        request = await self._request_repository.get_by_id_and_organization(
            request_id,
            organization_id,
        )
        if request is None:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        documents_count_by_request = await self._document_repository.count_by_request_ids(
            [request.id],
            organization_id=organization_id,
        )
        comments_count_by_request = (
            await self._request_comment_repository.count_by_request_ids(
                [request.id],
                organization_id=organization_id,
            )
        )
        customer_summary = None
        if request.customer_id is not None:
            customer = await self._customer_repository.get_by_id_and_organization(
                request.customer_id,
                organization_id,
            )
            if customer is not None:
                customer_summary = _to_customer_summary_read_model(customer)

        return _to_request_read_model(
            request,
            customer=customer_summary,
            documents_count=documents_count_by_request.get(request.id, 0),
            comments_count=comments_count_by_request.get(request.id, 0),
        )


class ListRequestsUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        document_repository: DocumentRepository,
        request_comment_repository: RequestCommentRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._request_repository = request_repository
        self._document_repository = document_repository
        self._request_comment_repository = request_comment_repository
        self._customer_repository = customer_repository

    async def execute(
        self,
        organization_id: UUID,
        filters: ListRequestsFilters,
        pagination: PaginationParams,
    ) -> PaginatedResult[RequestReadModel]:
        requests = await self._request_repository.list_by_organization_filters(
            organization_id,
            q=filters.q,
            status=filters.status,
            customer_id=filters.customer_id,
            assigned_membership_id=filters.assigned_membership_id,
            source=filters.source,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        total = await self._request_repository.count_by_organization_filters(
            organization_id,
            q=filters.q,
            status=filters.status,
            customer_id=filters.customer_id,
            assigned_membership_id=filters.assigned_membership_id,
            source=filters.source,
        )
        request_ids = [request.id for request in requests]
        documents_count_by_request = await self._document_repository.count_by_request_ids(
            request_ids,
            organization_id=organization_id,
        )
        comments_count_by_request = await self._request_comment_repository.count_by_request_ids(
            request_ids,
            organization_id=organization_id,
        )
        customers_by_id = {
            customer.id: _to_customer_summary_read_model(customer)
            for customer in await self._customer_repository.list_by_ids_and_organization(
                [
                    request.customer_id
                    for request in requests
                    if request.customer_id is not None
                ],
                organization_id,
            )
        }
        return PaginatedResult(
            items=[
                _to_request_read_model(
                    request,
                    customer=(
                        None
                        if request.customer_id is None
                        else customers_by_id.get(request.customer_id)
                    ),
                    documents_count=documents_count_by_request.get(request.id, 0),
                    comments_count=comments_count_by_request.get(request.id, 0),
                )
                for request in requests
            ],
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )


class UpdateRequestUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_activity_repository: RequestActivityRepository,
        document_repository: DocumentRepository,
        request_comment_repository: RequestCommentRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_activity_repository = request_activity_repository
        self._document_repository = document_repository
        self._request_comment_repository = request_comment_repository
        self._customer_repository = customer_repository

    async def execute(
        self,
        request_id: UUID,
        organization_id: UUID,
        command: UpdateRequestCommand,
    ) -> RequestReadModel:
        updatable_fields = {"title", "description", "customer_id"}
        provided_updatable_fields = command.model_fields_set.intersection(updatable_fields)
        if not provided_updatable_fields:
            raise ValidationError("At least one updatable field must be provided.")

        request = await self._request_repository.get_by_id_and_organization(
            request_id,
            organization_id,
        )
        if request is None:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        if "customer_id" in provided_updatable_fields and command.customer_id is not None:
            customer = await self._customer_repository.get_by_id_and_organization(
                command.customer_id,
                organization_id,
            )
            if customer is None:
                raise RequestCustomerNotFoundError(
                    f"Customer '{command.customer_id}' was not found."
                )

        changed_fields: list[str] = []
        if "title" in provided_updatable_fields and command.title != request.title:
            changed_fields.append("title")
        if (
            "description" in provided_updatable_fields
            and command.description != request.description
        ):
            changed_fields.append("description")
        if (
            "customer_id" in provided_updatable_fields
            and command.customer_id != request.customer_id
        ):
            changed_fields.append("customer_id")

        now = datetime.now(UTC)
        updated_request = Request(
            id=request.id,
            organization_id=request.organization_id,
            title=command.title if "title" in provided_updatable_fields else request.title,
            description=(
                command.description
                if "description" in provided_updatable_fields
                else request.description
            ),
            status=request.status,
            source=request.source,
            created_by_membership_id=request.created_by_membership_id,
            assigned_membership_id=request.assigned_membership_id,
            created_at=request.created_at,
            updated_at=now,
            customer_id=(
                command.customer_id
                if "customer_id" in provided_updatable_fields
                else request.customer_id
            ),
        )
        saved_request = await self._request_repository.update(updated_request)
        if changed_fields:
            await self._request_activity_repository.add(
                RequestActivity(
                    id=uuid4(),
                    request_id=saved_request.id,
                    organization_id=saved_request.organization_id,
                    membership_id=command.membership_id,
                    type=RequestActivityType.REQUEST_UPDATED,
                    payload={
                        "request_id": str(saved_request.id),
                        "actor_user_id": str(command.user_id),
                        "updated_fields": changed_fields,
                    },
                    created_at=now,
                )
            )
        await self._request_repository.save_changes()
        customer_summary = None
        if saved_request.customer_id is not None:
            customer = await self._customer_repository.get_by_id_and_organization(
                saved_request.customer_id,
                organization_id,
            )
            if customer is not None:
                customer_summary = _to_customer_summary_read_model(customer)

        documents_count_by_request = await self._document_repository.count_by_request_ids(
            [saved_request.id],
            organization_id=organization_id,
        )
        comments_count_by_request = (
            await self._request_comment_repository.count_by_request_ids(
                [saved_request.id],
                organization_id=organization_id,
            )
        )
        return _to_request_read_model(
            saved_request,
            customer=customer_summary,
            documents_count=documents_count_by_request.get(saved_request.id, 0),
            comments_count=comments_count_by_request.get(saved_request.id, 0),
        )


class TransitionRequestStatusUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_activity_repository: RequestActivityRepository,
        organization_membership_repository: OrganizationMembershipRepository,
        request_status_history_repository: RequestStatusHistoryRepository,
        document_repository: DocumentRepository,
        request_comment_repository: RequestCommentRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_activity_repository = request_activity_repository
        self._organization_membership_repository = organization_membership_repository
        self._request_status_history_repository = request_status_history_repository
        self._document_repository = document_repository
        self._request_comment_repository = request_comment_repository
        self._customer_repository = customer_repository

    async def execute(
        self,
        request_id: UUID,
        command: TransitionRequestStatusCommand,
    ) -> RequestReadModel:
        request = await self._request_repository.get_by_id_and_organization(
            request_id,
            command.organization_id,
        )
        if request is None:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

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
            organization_id=request.organization_id,
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
        await self._request_status_history_repository.add(
            RequestStatusHistoryEntry(
                id=uuid4(),
                request_id=updated_request.id,
                organization_id=updated_request.organization_id,
                previous_status=request.status,
                new_status=command.new_status,
                changed_at=now,
                changed_by=command.membership_id,
                changed_by_user_id=command.user_id,
            )
        )
        await self._request_repository.save_changes()
        documents_count_by_request = await self._document_repository.count_by_request_ids(
            [updated_request.id],
            organization_id=updated_request.organization_id,
        )
        comments_count_by_request = (
            await self._request_comment_repository.count_by_request_ids(
                [updated_request.id],
                organization_id=updated_request.organization_id,
            )
        )
        customer_summary = None
        if updated_request.customer_id is not None:
            customer = await self._customer_repository.get_by_id_and_organization(
                updated_request.customer_id,
                updated_request.organization_id,
            )
            if customer is not None:
                customer_summary = _to_customer_summary_read_model(customer)
        return _to_request_read_model(
            updated_request,
            customer=customer_summary,
            documents_count=documents_count_by_request.get(updated_request.id, 0),
            comments_count=comments_count_by_request.get(updated_request.id, 0),
        )


class AssignRequestUseCase:
    def __init__(
        self,
        request_repository: RequestRepository,
        request_activity_repository: RequestActivityRepository,
        organization_membership_repository: OrganizationMembershipRepository,
        document_repository: DocumentRepository,
        request_comment_repository: RequestCommentRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._request_repository = request_repository
        self._request_activity_repository = request_activity_repository
        self._organization_membership_repository = organization_membership_repository
        self._document_repository = document_repository
        self._request_comment_repository = request_comment_repository
        self._customer_repository = customer_repository

    async def execute(
        self,
        request_id: UUID,
        command: AssignRequestCommand,
    ) -> RequestReadModel:
        request = await self._request_repository.get_by_id(request_id)
        if request is None:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        if request.organization_id != command.organization_id:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        actor_membership = await self._organization_membership_repository.get_by_id(
            command.membership_id
        )
        if actor_membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{command.membership_id}' was not found."
            )

        if actor_membership.organization_id != command.organization_id:
            raise RequestMembershipOrganizationMismatchError(
                "The provided membership does not belong to the provided organization."
            )

        assigned_membership = await self._organization_membership_repository.get_by_id(
            command.assigned_membership_id
        )
        if assigned_membership is None:
            raise OrganizationMembershipNotFoundError(
                f"Membership '{command.assigned_membership_id}' was not found."
            )

        if assigned_membership.organization_id != command.organization_id:
            raise RequestAssignedMembershipOrganizationMismatchError(
                "The assigned membership does not belong to the provided organization."
            )

        now = datetime.now(UTC)
        updated_request = await self._request_repository.update_assignment(
            request_id=request.id,
            assigned_membership_id=assigned_membership.id,
            updated_at=now,
        )
        await self._request_activity_repository.add(
            RequestActivity(
                id=uuid4(),
                request_id=updated_request.id,
                organization_id=updated_request.organization_id,
                membership_id=command.membership_id,
                type=RequestActivityType.REQUEST_ASSIGNED,
                payload={
                    "assigned_membership_id": str(assigned_membership.id),
                },
                created_at=now,
            )
        )
        await self._request_repository.save_changes()
        documents_count_by_request = await self._document_repository.count_by_request_ids(
            [updated_request.id],
            organization_id=updated_request.organization_id,
        )
        comments_count_by_request = (
            await self._request_comment_repository.count_by_request_ids(
                [updated_request.id],
                organization_id=updated_request.organization_id,
            )
        )
        customer_summary = None
        if updated_request.customer_id is not None:
            customer = await self._customer_repository.get_by_id_and_organization(
                updated_request.customer_id,
                updated_request.organization_id,
            )
            if customer is not None:
                customer_summary = _to_customer_summary_read_model(customer)
        return _to_request_read_model(
            updated_request,
            customer=customer_summary,
            documents_count=documents_count_by_request.get(updated_request.id, 0),
            comments_count=comments_count_by_request.get(updated_request.id, 0),
        )


class ListRequestActivitiesUseCase:
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
        organization_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResult[RequestActivityReadModel]:
        request = await self._request_repository.get_by_id_and_organization(
            request_id,
            organization_id,
        )
        if request is None:
            raise RequestNotFoundError(f"Request '{request_id}' was not found.")

        activities = await self._request_activity_repository.list_by_request_id(
            request_id,
            organization_id=organization_id,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        total = await self._request_activity_repository.count_by_request_id(
            request_id,
            organization_id=organization_id,
        )
        memberships_by_id = {
            membership.id: membership.user_id
            for membership in await self._organization_membership_repository.list_by_ids_and_organization(
                [activity.membership_id for activity in activities],
                organization_id,
            )
        }
        return PaginatedResult(
            items=[
                _to_request_activity_read_model(
                    activity,
                    actor_user_id=memberships_by_id.get(activity.membership_id),
                )
                for activity in activities
            ],
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )
