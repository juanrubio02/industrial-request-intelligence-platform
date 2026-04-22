from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.documents.commands import CreateDocumentCommand
from app.application.documents.commands import EnqueueDocumentProcessingCommand
from app.application.documents.commands import UploadDocumentCommand
from app.application.documents.exceptions import (
    DocumentMembershipOrganizationMismatchError,
    DocumentNotFoundError,
    DocumentRequestOrganizationMismatchError,
    DocumentUploadInvalidFileError,
)
from app.application.documents.processing import DocumentProcessingDispatcher
from app.application.documents.services import (
    CreateDocumentUseCase,
    EnqueueDocumentProcessingUseCase,
    UploadDocumentUseCase,
)
from app.application.documents.storage import DocumentStorage, generate_storage_key
from app.application.organization_memberships.exceptions import (
    OrganizationMembershipNotFoundError,
)
from app.application.requests.exceptions import RequestNotFoundError
from app.domain.documents.entities import Document
from app.domain.documents.repositories import DocumentRepository
from app.domain.documents.statuses import DocumentProcessingStatus
from app.domain.organization_memberships.entities import OrganizationMembership
from app.domain.organization_memberships.repositories import OrganizationMembershipRepository
from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus
from app.domain.request_activities.entities import RequestActivity
from app.domain.request_activities.repositories import RequestActivityRepository
from app.domain.request_activities.types import RequestActivityType
from app.domain.requests.entities import Request
from app.domain.requests.repositories import RequestRepository
from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus


class InMemoryRequestRepository(RequestRepository):
    def __init__(self, requests: list[Request] | None = None) -> None:
        self._requests = {request.id: request for request in requests or []}

    async def add(self, request: Request) -> Request:
        self._requests[request.id] = request
        return request

    async def save_changes(self) -> None:
        return None

    async def get_by_id(self, request_id):
        return self._requests.get(request_id)

    async def get_by_id_and_organization(self, request_id, organization_id):
        request = self._requests.get(request_id)
        if request is None or request.organization_id != organization_id:
            return None
        return request

    async def list_by_organization_id(self, organization_id):
        return [
            request
            for request in self._requests.values()
            if request.organization_id == organization_id
        ]

    async def list_by_organization_filters(
        self,
        organization_id,
        *,
        q=None,
        status=None,
        customer_id=None,
        assigned_membership_id=None,
        source=None,
        limit=None,
        offset=0,
    ):
        requests = await self.list_by_organization_id(organization_id)
        if q:
            requests = [request for request in requests if q.lower() in request.title.lower()]
        if status:
            requests = [request for request in requests if request.status == status]
        if customer_id:
            requests = [request for request in requests if request.customer_id == customer_id]
        if assigned_membership_id:
            requests = [
                request
                for request in requests
                if request.assigned_membership_id == assigned_membership_id
            ]
        if source:
            requests = [request for request in requests if request.source == source]
        end = None if limit is None else offset + limit
        return requests[offset:end]

    async def count_by_organization_filters(
        self,
        organization_id,
        *,
        q=None,
        status=None,
        customer_id=None,
        assigned_membership_id=None,
        source=None,
    ):
        requests = await self.list_by_organization_filters(
            organization_id,
            q=q,
            status=status,
            customer_id=customer_id,
            assigned_membership_id=assigned_membership_id,
            source=source,
        )
        return len(requests)

    async def update(self, request: Request) -> Request:
        self._requests[request.id] = request
        return request

    async def update_status(self, request_id, organization_id, new_status, updated_at):
        request = self._requests[request_id]
        if request.organization_id != organization_id:
            raise ValueError(f"Request '{request_id}' was not found.")
        updated_request = Request(
            id=request.id,
            organization_id=request.organization_id,
            title=request.title,
            description=request.description,
            status=new_status,
            source=request.source,
            created_by_membership_id=request.created_by_membership_id,
            assigned_membership_id=request.assigned_membership_id,
            created_at=request.created_at,
            updated_at=updated_at,
            customer_id=request.customer_id,
        )
        self._requests[request_id] = updated_request
        return updated_request

    async def update_assignment(self, request_id, assigned_membership_id, updated_at):
        request = self._requests[request_id]
        updated_request = Request(
            id=request.id,
            organization_id=request.organization_id,
            title=request.title,
            description=request.description,
            status=request.status,
            source=request.source,
            created_by_membership_id=request.created_by_membership_id,
            assigned_membership_id=assigned_membership_id,
            created_at=request.created_at,
            updated_at=updated_at,
            customer_id=request.customer_id,
        )
        self._requests[request_id] = updated_request
        return updated_request


class InMemoryDocumentRepository(DocumentRepository):
    def __init__(self) -> None:
        self.documents: list[Document] = []

    async def add(self, document: Document) -> Document:
        self.documents.append(document)
        return document

    async def save_changes(self) -> None:
        return None

    async def get_by_id(self, document_id):
        for document in self.documents:
            if document.id == document_id:
                return document
        return None

    async def list_by_request_id(
        self,
        request_id,
        *,
        organization_id,
        limit=None,
        offset=0,
    ):
        documents = [
            document
            for document in self.documents
            if document.request_id == request_id and document.organization_id == organization_id
        ]
        end = None if limit is None else offset + limit
        return documents[offset:end]

    async def count_by_request_id(self, request_id, *, organization_id):
        return sum(
            1
            for document in self.documents
            if document.request_id == request_id and document.organization_id == organization_id
        )

    async def count_by_request_ids(self, request_ids, *, organization_id):
        return {
            request_id: sum(
                1
                for document in self.documents
                if document.request_id == request_id
                and document.organization_id == organization_id
            )
            for request_id in request_ids
        }

    async def update_processing_status(self, document_id, new_status, updated_at):
        for index, document in enumerate(self.documents):
            if document.id == document_id:
                updated_document = Document(
                    id=document.id,
                    request_id=document.request_id,
                    organization_id=document.organization_id,
                    uploaded_by_membership_id=document.uploaded_by_membership_id,
                    original_filename=document.original_filename,
                    storage_key=document.storage_key,
                    content_type=document.content_type,
                    size_bytes=document.size_bytes,
                    processing_status=new_status,
                    verified_structured_data=document.verified_structured_data,
                    created_at=document.created_at,
                    updated_at=updated_at,
                )
                self.documents[index] = updated_document
                return updated_document
        raise ValueError(f"Document '{document_id}' was not found.")

    async def update_verified_structured_data(
        self,
        document_id,
        verified_structured_data,
        updated_at,
    ):
        for index, document in enumerate(self.documents):
            if document.id == document_id:
                updated_document = Document(
                    id=document.id,
                    request_id=document.request_id,
                    organization_id=document.organization_id,
                    uploaded_by_membership_id=document.uploaded_by_membership_id,
                    original_filename=document.original_filename,
                    storage_key=document.storage_key,
                    content_type=document.content_type,
                    size_bytes=document.size_bytes,
                    processing_status=document.processing_status,
                    verified_structured_data=verified_structured_data,
                    created_at=document.created_at,
                    updated_at=updated_at,
                )
                self.documents[index] = updated_document
                return updated_document
        raise ValueError(f"Document '{document_id}' was not found.")


class InMemoryOrganizationMembershipRepository(OrganizationMembershipRepository):
    def __init__(self, memberships: list[OrganizationMembership] | None = None) -> None:
        self._memberships = {membership.id: membership for membership in memberships or []}

    async def add(self, membership: OrganizationMembership) -> OrganizationMembership:
        self._memberships[membership.id] = membership
        return membership

    async def get_by_id(self, membership_id):
        return self._memberships.get(membership_id)

    async def get_by_id_and_organization(self, membership_id, organization_id):
        membership = self._memberships.get(membership_id)
        if membership is None or membership.organization_id != organization_id:
            return None
        return membership

    async def get_active_by_user_and_organization(self, user_id, organization_id):
        for membership in self._memberships.values():
            if (
                membership.user_id == user_id
                and membership.organization_id == organization_id
                and membership.is_active
            ):
                return membership
        return None

    async def list_active_by_user_id(self, user_id, *, limit=None, offset=0):
        memberships = [
            membership
            for membership in self._memberships.values()
            if membership.user_id == user_id and membership.is_active
        ]
        end = None if limit is None else offset + limit
        return memberships[offset:end]

    async def count_active_by_user_id(self, user_id):
        return sum(
            1
            for membership in self._memberships.values()
            if membership.user_id == user_id and membership.is_active
        )

    async def list_active_by_organization_id(self, organization_id, *, limit=None, offset=0):
        memberships = [
            membership
            for membership in self._memberships.values()
            if membership.organization_id == organization_id and membership.is_active
        ]
        end = None if limit is None else offset + limit
        return memberships[offset:end]

    async def list_by_organization_id(self, organization_id, *, limit=None, offset=0):
        memberships = [
            membership
            for membership in self._memberships.values()
            if membership.organization_id == organization_id
        ]
        end = None if limit is None else offset + limit
        return memberships[offset:end]

    async def count_by_organization_id(self, organization_id):
        return sum(
            1
            for membership in self._memberships.values()
            if membership.organization_id == organization_id
        )

    async def list_by_ids_and_organization(self, membership_ids, organization_id):
        return [
            membership
            for membership_id in membership_ids
            if (membership := self._memberships.get(membership_id)) is not None
            and membership.organization_id == organization_id
        ]

    async def save(self, membership: OrganizationMembership) -> OrganizationMembership:
        self._memberships[membership.id] = membership
        return membership

    async def count_active_by_organization_and_role(self, organization_id, role):
        return sum(
            1
            for membership in self._memberships.values()
            if membership.organization_id == organization_id
            and membership.role == role
            and membership.is_active
        )


class InMemoryRequestActivityRepository(RequestActivityRepository):
    def __init__(self) -> None:
        self.activities: list[RequestActivity] = []

    async def add(self, activity: RequestActivity) -> RequestActivity:
        self.activities.append(activity)
        return activity

    async def list_by_request_id(
        self,
        request_id,
        *,
        organization_id,
        limit=None,
        offset=0,
    ):
        activities = [
            activity
            for activity in self.activities
            if activity.request_id == request_id
            and activity.organization_id == organization_id
        ]
        end = None if limit is None else offset + limit
        return activities[offset:end]

    async def count_by_request_id(self, request_id, *, organization_id):
        return sum(
            1
            for activity in self.activities
            if activity.request_id == request_id and activity.organization_id == organization_id
        )


class InMemoryDocumentStorage(DocumentStorage):
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def save(self, *, storage_key: str, content: bytes, content_type: str) -> None:
        self.files[storage_key] = content

    async def delete(self, *, storage_key: str) -> None:
        self.files.pop(storage_key, None)

    async def read(self, *, storage_key: str) -> bytes:
        return self.files[storage_key]


class InMemoryDocumentProcessingDispatcher(DocumentProcessingDispatcher):
    def __init__(self) -> None:
        self.enqueued_jobs: list[tuple[object, object]] = []

    async def enqueue(self, document_id, organization_id) -> None:
        self.enqueued_jobs.append((document_id, organization_id))


def _request(organization_id) -> Request:
    now = datetime.now(UTC)
    return Request(
        id=uuid4(),
        organization_id=organization_id,
        title="Need pumps",
        description="Original request",
        status=RequestStatus.NEW,
        source=RequestSource.EMAIL,
        created_by_membership_id=uuid4(),
        assigned_membership_id=None,
        created_at=now,
        updated_at=now,
    )


def _membership(organization_id) -> OrganizationMembership:
    now = datetime.now(UTC)
    return OrganizationMembership(
        id=uuid4(),
        organization_id=organization_id,
        user_id=uuid4(),
        role=OrganizationMembershipRole.ADMIN,
        status=OrganizationMembershipStatus.ACTIVE,
        joined_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_create_document_use_case_creates_pending_document_and_activity() -> None:
    organization_id = uuid4()
    request = _request(organization_id)
    membership = _membership(organization_id)
    activity_repository = InMemoryRequestActivityRepository()
    use_case = CreateDocumentUseCase(
        document_repository=InMemoryDocumentRepository(),
        request_repository=InMemoryRequestRepository([request]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_activity_repository=activity_repository,
    )

    result = await use_case.execute(
        CreateDocumentCommand(
            request_id=request.id,
            organization_id=organization_id,
            uploaded_by_membership_id=membership.id,
            original_filename="quote.pdf",
            content_type="application/pdf",
            size_bytes=1024,
        )
    )

    assert result.request_id == request.id
    assert result.organization_id == organization_id
    assert result.uploaded_by_membership_id == membership.id
    assert result.original_filename == "quote.pdf"
    assert result.storage_key.startswith("documents/")
    assert result.storage_key.endswith(".pdf")
    assert result.processing_status == DocumentProcessingStatus.PENDING
    assert len(activity_repository.activities) == 1
    activity = activity_repository.activities[0]
    assert activity.type == RequestActivityType.DOCUMENT_UPLOADED
    assert activity.payload["document_id"] == str(result.id)
    assert activity.payload["storage_key"] == result.storage_key
    assert activity.payload["processing_status"] == DocumentProcessingStatus.PENDING.value


@pytest.mark.anyio
async def test_upload_document_use_case_stores_file_and_creates_document() -> None:
    organization_id = uuid4()
    request = _request(organization_id)
    membership = _membership(organization_id)
    document_repository = InMemoryDocumentRepository()
    activity_repository = InMemoryRequestActivityRepository()
    storage = InMemoryDocumentStorage()
    create_document_use_case = CreateDocumentUseCase(
        document_repository=document_repository,
        request_repository=InMemoryRequestRepository([request]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_activity_repository=activity_repository,
    )
    upload_use_case = UploadDocumentUseCase(
        document_storage=storage,
        create_document_use_case=create_document_use_case,
    )

    result = await upload_use_case.execute(
        UploadDocumentCommand(
            request_id=request.id,
            organization_id=organization_id,
            uploaded_by_membership_id=membership.id,
            original_filename="quote.pdf",
            content_type="application/pdf",
            content=b"pdf-content",
        )
    )

    assert result.processing_status == DocumentProcessingStatus.PENDING
    assert result.size_bytes == 11
    assert result.storage_key.startswith("documents/")
    assert result.storage_key.endswith(".pdf")
    assert result.storage_key in storage.files
    assert storage.files[result.storage_key] == b"pdf-content"
    assert activity_repository.activities[0].type == RequestActivityType.DOCUMENT_UPLOADED


def test_generate_storage_key_uses_safe_extension_only() -> None:
    assert generate_storage_key("quote.PDF").endswith(".pdf")
    assert generate_storage_key("../../etc/passwd").count("/") == 1
    assert not generate_storage_key("invoice.tx$t").endswith(".tx$t")


@pytest.mark.anyio
async def test_upload_document_use_case_rejects_empty_file() -> None:
    organization_id = uuid4()
    request = _request(organization_id)
    membership = _membership(organization_id)
    create_document_use_case = CreateDocumentUseCase(
        document_repository=InMemoryDocumentRepository(),
        request_repository=InMemoryRequestRepository([request]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_activity_repository=InMemoryRequestActivityRepository(),
    )
    upload_use_case = UploadDocumentUseCase(
        document_storage=InMemoryDocumentStorage(),
        create_document_use_case=create_document_use_case,
    )

    with pytest.raises(DocumentUploadInvalidFileError):
        await upload_use_case.execute(
            UploadDocumentCommand(
                request_id=request.id,
                organization_id=organization_id,
                uploaded_by_membership_id=membership.id,
                original_filename="empty.pdf",
                content_type="application/pdf",
                content=b"",
            )
        )


@pytest.mark.anyio
async def test_enqueue_document_processing_use_case_enqueues_pending_document() -> None:
    organization_id = uuid4()
    request = _request(organization_id)
    membership = _membership(organization_id)
    document_repository = InMemoryDocumentRepository()
    create_document_use_case = CreateDocumentUseCase(
        document_repository=document_repository,
        request_repository=InMemoryRequestRepository([request]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_activity_repository=InMemoryRequestActivityRepository(),
    )
    created_document = await create_document_use_case.execute(
        CreateDocumentCommand(
            request_id=request.id,
            organization_id=organization_id,
            uploaded_by_membership_id=membership.id,
            original_filename="quote.pdf",
            content_type="application/pdf",
            size_bytes=128,
        )
    )
    dispatcher = InMemoryDocumentProcessingDispatcher()
    enqueue_use_case = EnqueueDocumentProcessingUseCase(
        document_repository=document_repository,
        document_processing_dispatcher=dispatcher,
    )

    result = await enqueue_use_case.execute(
        EnqueueDocumentProcessingCommand(
            document_id=created_document.id,
            organization_id=organization_id,
        )
    )

    assert result.document_id == created_document.id
    assert result.processing_status == DocumentProcessingStatus.PENDING
    assert dispatcher.enqueued_jobs == [(created_document.id, organization_id)]


@pytest.mark.anyio
async def test_enqueue_document_processing_use_case_rejects_missing_document() -> None:
    enqueue_use_case = EnqueueDocumentProcessingUseCase(
        document_repository=InMemoryDocumentRepository(),
        document_processing_dispatcher=InMemoryDocumentProcessingDispatcher(),
    )

    with pytest.raises(DocumentNotFoundError):
        await enqueue_use_case.execute(
            EnqueueDocumentProcessingCommand(
                document_id=uuid4(),
                organization_id=uuid4(),
            )
        )


@pytest.mark.anyio
async def test_create_document_use_case_rejects_missing_request() -> None:
    organization_id = uuid4()
    membership = _membership(organization_id)
    use_case = CreateDocumentUseCase(
        document_repository=InMemoryDocumentRepository(),
        request_repository=InMemoryRequestRepository(),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_activity_repository=InMemoryRequestActivityRepository(),
    )

    with pytest.raises(RequestNotFoundError):
        await use_case.execute(
            CreateDocumentCommand(
                request_id=uuid4(),
                organization_id=organization_id,
                uploaded_by_membership_id=membership.id,
                original_filename="missing.pdf",
                content_type="application/pdf",
                size_bytes=512,
            )
        )


@pytest.mark.anyio
async def test_create_document_use_case_rejects_missing_membership() -> None:
    organization_id = uuid4()
    request = _request(organization_id)
    use_case = CreateDocumentUseCase(
        document_repository=InMemoryDocumentRepository(),
        request_repository=InMemoryRequestRepository([request]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository(),
        request_activity_repository=InMemoryRequestActivityRepository(),
    )

    with pytest.raises(OrganizationMembershipNotFoundError):
        await use_case.execute(
            CreateDocumentCommand(
                request_id=request.id,
                organization_id=organization_id,
                uploaded_by_membership_id=uuid4(),
                original_filename="missing-membership.pdf",
                content_type="application/pdf",
                size_bytes=512,
            )
        )


@pytest.mark.anyio
async def test_create_document_use_case_rejects_membership_from_other_organization() -> None:
    organization_id = uuid4()
    other_organization_id = uuid4()
    request = _request(organization_id)
    membership = _membership(other_organization_id)
    use_case = CreateDocumentUseCase(
        document_repository=InMemoryDocumentRepository(),
        request_repository=InMemoryRequestRepository([request]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_activity_repository=InMemoryRequestActivityRepository(),
    )

    with pytest.raises(DocumentMembershipOrganizationMismatchError):
        await use_case.execute(
            CreateDocumentCommand(
                request_id=request.id,
                organization_id=organization_id,
                uploaded_by_membership_id=membership.id,
                original_filename="cross-org.pdf",
                content_type="application/pdf",
                size_bytes=512,
            )
        )


@pytest.mark.anyio
async def test_create_document_use_case_rejects_request_from_other_organization() -> None:
    request = _request(uuid4())
    membership = _membership(request.organization_id)
    other_organization_id = uuid4()
    use_case = CreateDocumentUseCase(
        document_repository=InMemoryDocumentRepository(),
        request_repository=InMemoryRequestRepository([request]),
        organization_membership_repository=InMemoryOrganizationMembershipRepository([membership]),
        request_activity_repository=InMemoryRequestActivityRepository(),
    )

    with pytest.raises(DocumentRequestOrganizationMismatchError):
        await use_case.execute(
            CreateDocumentCommand(
                request_id=request.id,
                organization_id=other_organization_id,
                uploaded_by_membership_id=membership.id,
                original_filename="wrong-org.pdf",
                content_type="application/pdf",
                size_bytes=512,
            )
        )
