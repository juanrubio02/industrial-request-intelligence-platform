from datetime import UTC, datetime
from uuid import UUID
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.document_processing_results.entities import DocumentProcessingResult
from app.domain.document_processing_results.document_types import (
    DocumentDetectedType,
)
from app.domain.document_processing_results.statuses import (
    DocumentProcessingResultStatus,
)
from app.domain.requests.sources import RequestSource
from app.infrastructure.document_processing_results.repositories import (
    SqlAlchemyDocumentProcessingResultRepository,
)


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
        files={"file": ("specification.pdf", b"binary-pdf-content", "application/pdf")},
        headers=_membership_headers(access_token, membership_id),
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_document_processing_result_repository_persists_success_result(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(
        api_client, "Processing Result Success", "processing-result-success"
    )
    user = await _create_user(
        api_client,
        "processing-result-success@example.com",
        "Processing Result Success",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-result-success@example.com")
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
    now = datetime.now(UTC)

    async with session_factory() as session:
        repository = SqlAlchemyDocumentProcessingResultRepository(session=session)
        await repository.upsert(
            DocumentProcessingResult(
                id=uuid4(),
                document_id=UUID(document_payload["id"]),
                organization_id=UUID(organization["id"]),
                status=DocumentProcessingResultStatus.PROCESSED,
                extracted_text="Extracted specification text.",
                summary="Specification summary.",
                detected_document_type=DocumentDetectedType.TECHNICAL_SPEC,
                structured_data={"language": "en", "pages": 2},
                error_message=None,
                processed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        await repository.save_changes()
        stored_result = await repository.get_by_document_id(UUID(document_payload["id"]))

    assert stored_result is not None
    assert stored_result.document_id == UUID(document_payload["id"])
    assert stored_result.organization_id == UUID(organization["id"])
    assert stored_result.status == DocumentProcessingResultStatus.PROCESSED
    assert stored_result.summary == "Specification summary."
    assert stored_result.structured_data == {"language": "en", "pages": 2}


@pytest.mark.anyio
async def test_document_processing_result_repository_persists_failed_result(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(
        api_client, "Processing Result Failed", "processing-result-failed"
    )
    user = await _create_user(
        api_client,
        "processing-result-failed@example.com",
        "Processing Result Failed",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-result-failed@example.com")
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
    now = datetime.now(UTC)

    async with session_factory() as session:
        repository = SqlAlchemyDocumentProcessingResultRepository(session=session)
        await repository.upsert(
            DocumentProcessingResult(
                id=uuid4(),
                document_id=UUID(document_payload["id"]),
                organization_id=UUID(organization["id"]),
                status=DocumentProcessingResultStatus.FAILED,
                extracted_text=None,
                summary=None,
                detected_document_type=None,
                structured_data=None,
                error_message="Processing failed due to invalid format.",
                processed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        await repository.save_changes()
        stored_result = await repository.get_by_document_id(UUID(document_payload["id"]))

    assert stored_result is not None
    assert stored_result.document_id == UUID(document_payload["id"])
    assert stored_result.status == DocumentProcessingResultStatus.FAILED
    assert stored_result.error_message == "Processing failed due to invalid format."
    assert stored_result.extracted_text is None


@pytest.mark.anyio
async def test_document_processing_result_repository_gets_result_by_document_id(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(
        api_client, "Processing Result Lookup", "processing-result-lookup"
    )
    user = await _create_user(
        api_client,
        "processing-result-lookup@example.com",
        "Processing Result Lookup",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-result-lookup@example.com")
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
    now = datetime.now(UTC)

    async with session_factory() as session:
        repository = SqlAlchemyDocumentProcessingResultRepository(session=session)
        await repository.upsert(
            DocumentProcessingResult(
                id=uuid4(),
                document_id=UUID(document_payload["id"]),
                organization_id=UUID(organization["id"]),
                status=DocumentProcessingResultStatus.PROCESSED,
                extracted_text="Lookup text",
                summary=None,
                detected_document_type=None,
                structured_data={"lookup": True},
                error_message=None,
                processed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        await repository.save_changes()
        stored_result = await repository.get_by_document_id(UUID(document_payload["id"]))

    assert stored_result is not None
    assert stored_result.document_id == UUID(document_payload["id"])
    assert stored_result.structured_data == {"lookup": True}
