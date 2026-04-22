from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.documents.processing import DocumentProcessingOutput, DocumentProcessor
from app.domain.document_processing_jobs.statuses import DocumentProcessingJobStatus
from app.domain.documents.statuses import DocumentProcessingStatus
from app.domain.requests.sources import RequestSource
from app.infrastructure.database.models.document_processing_job import (
    DocumentProcessingJobModel,
)
from app.infrastructure.document_processing.worker import DocumentProcessingWorker
from app.infrastructure.document_processing_jobs.repositories import (
    SqlAlchemyDocumentProcessingJobRepository,
)
from app.infrastructure.documents.repositories import SqlAlchemyDocumentRepository


class NoOpDocumentProcessor(DocumentProcessor):
    async def process(self, document) -> DocumentProcessingOutput:
        return DocumentProcessingOutput(extracted_text="processed")


class FailingDocumentProcessor(DocumentProcessor):
    async def process(self, document) -> DocumentProcessingOutput:
        raise RuntimeError("Document processing failed.")


async def _create_organization(api_client: AsyncClient, name: str, slug: str) -> dict:
    response = await api_client.post("/organizations", json={"name": name, "slug": slug})
    assert response.status_code == 201
    return response.json()


async def _create_user(
    api_client: AsyncClient,
    email: str,
    full_name: str,
    password: str = "StrongPass123!",
) -> dict:
    response = await api_client.post(
        "/users",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert response.status_code == 201
    return response.json()


async def _login(
    api_client: AsyncClient,
    email: str,
    password: str = "StrongPass123!",
) -> dict:
    response = await api_client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def _membership_headers(access_token: str, membership_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Membership-Id": membership_id,
    }


async def _create_membership(
    api_client: AsyncClient,
    organization_id: str,
    user_id: str,
    role: str = "ADMIN",
) -> dict:
    response = await api_client.post(
        f"/organizations/{organization_id}/memberships",
        json={"user_id": user_id, "role": role},
    )
    assert response.status_code == 201
    return response.json()


async def _create_request(
    api_client: AsyncClient,
    membership_id: str,
    access_token: str,
) -> dict:
    response = await api_client.post(
        "/requests",
        json={
            "title": "Need industrial filters",
            "description": "Initial request payload",
            "source": RequestSource.EMAIL.value,
        },
        headers=_membership_headers(access_token, membership_id),
    )
    assert response.status_code == 201
    return response.json()


async def _create_document(
    api_client: AsyncClient,
    request_id: str,
    membership_id: str,
    access_token: str,
) -> dict:
    response = await api_client.post(
        f"/requests/{request_id}/documents/upload",
        files={"file": ("specification.txt", b"Industrial request text content.", "text/plain")},
        headers=_membership_headers(access_token, membership_id),
    )
    assert response.status_code == 201
    return response.json()


async def _create_document_ready_for_processing(api_client: AsyncClient) -> tuple[dict, dict]:
    organization = await _create_organization(
        api_client,
        "Document Jobs Org",
        "document-jobs-org",
    )
    user = await _create_user(api_client, "document-jobs@example.com", "Document Jobs")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "document-jobs@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )
    document_payload = await _create_document(
        api_client,
        request_payload["id"],
        membership["id"],
        auth_payload["access_token"],
    )
    headers = _membership_headers(auth_payload["access_token"], membership["id"])
    return document_payload, {"organization": organization, "headers": headers}


@pytest.mark.anyio
async def test_post_document_processing_jobs_creates_durable_job(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    document_payload, context = await _create_document_ready_for_processing(api_client)

    response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=context["headers"],
    )

    assert response.status_code == 202
    assert response.json()["document_id"] == document_payload["id"]
    assert response.json()["processing_status"] == DocumentProcessingStatus.PENDING.value

    async with session_factory() as session:
        job_repository = SqlAlchemyDocumentProcessingJobRepository(session=session)
        job = await job_repository.get_active_by_document_id(UUID(document_payload["id"]))

    assert job is not None
    assert job.organization_id == UUID(context["organization"]["id"])
    assert job.status == DocumentProcessingJobStatus.PENDING
    assert job.attempts == 0


@pytest.mark.anyio
async def test_post_document_processing_jobs_does_not_duplicate_active_job(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    document_payload, context = await _create_document_ready_for_processing(api_client)

    first_response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=context["headers"],
    )
    second_response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=context["headers"],
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 202

    async with session_factory() as session:
        count = await session.scalar(
            select(func.count(DocumentProcessingJobModel.id)).where(
                DocumentProcessingJobModel.document_id == UUID(document_payload["id"])
            )
        )

    assert int(count or 0) == 1


@pytest.mark.anyio
async def test_document_processing_job_repository_claims_next_pending_job(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    document_payload, context = await _create_document_ready_for_processing(api_client)
    enqueue_response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=context["headers"],
    )
    assert enqueue_response.status_code == 202

    async with session_factory() as session:
        job_repository = SqlAlchemyDocumentProcessingJobRepository(session=session)
        claimed_job = await job_repository.get_next_pending_job()
        await job_repository.save_changes()

    assert claimed_job is not None
    assert claimed_job.document_id == UUID(document_payload["id"])
    assert claimed_job.status == DocumentProcessingJobStatus.PROCESSING
    assert claimed_job.attempts == 1
    assert claimed_job.locked_at is not None


@pytest.mark.anyio
async def test_document_processing_worker_processes_job_and_marks_completed(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    document_payload, context = await _create_document_ready_for_processing(api_client)
    enqueue_response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=context["headers"],
    )
    assert enqueue_response.status_code == 202

    worker = DocumentProcessingWorker(
        session_factory=session_factory,
        document_processor=NoOpDocumentProcessor(),
    )
    claimed_job = await worker.process_next_job()

    assert claimed_job is not None

    async with session_factory() as session:
        job_repository = SqlAlchemyDocumentProcessingJobRepository(session=session)
        document_repository = SqlAlchemyDocumentRepository(session=session)
        stored_job = await job_repository.get_by_id(claimed_job.id)
        document = await document_repository.get_by_id(UUID(document_payload["id"]))

    assert stored_job is not None
    assert stored_job.status == DocumentProcessingJobStatus.COMPLETED
    assert document is not None
    assert document.processing_status == DocumentProcessingStatus.PROCESSED


@pytest.mark.anyio
async def test_document_processing_worker_marks_job_failed_on_error(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    document_payload, context = await _create_document_ready_for_processing(api_client)
    enqueue_response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=context["headers"],
    )
    assert enqueue_response.status_code == 202

    worker = DocumentProcessingWorker(
        session_factory=session_factory,
        document_processor=FailingDocumentProcessor(),
    )
    claimed_job = await worker.process_next_job()

    assert claimed_job is not None

    async with session_factory() as session:
        job_repository = SqlAlchemyDocumentProcessingJobRepository(session=session)
        document_repository = SqlAlchemyDocumentRepository(session=session)
        stored_job = await job_repository.get_by_id(claimed_job.id)
        document = await document_repository.get_by_id(UUID(document_payload["id"]))

    assert stored_job is not None
    assert stored_job.status == DocumentProcessingJobStatus.FAILED
    assert document is not None
    assert document.processing_status == DocumentProcessingStatus.FAILED
