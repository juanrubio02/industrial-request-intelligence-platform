from uuid import UUID
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.documents.processing import DocumentProcessingOutput
from app.application.documents.processing import DocumentProcessor
from app.application.documents.services import ProcessDocumentUseCase
from app.domain.document_processing_results.document_types import (
    DocumentDetectedType,
)
from app.domain.requests.sources import RequestSource
from app.infrastructure.document_processing_results.repositories import (
    SqlAlchemyDocumentProcessingResultRepository,
)
from app.infrastructure.documents.repositories import SqlAlchemyDocumentRepository


class ApiSuccessfulDocumentProcessor(DocumentProcessor):
    async def process(self, document) -> DocumentProcessingOutput:
        return DocumentProcessingOutput(
            extracted_text="API extracted text.",
            summary="API summary.",
            detected_document_type=DocumentDetectedType.OTHER,
            structured_data={"source": "api-test"},
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
async def test_get_document_processing_result_returns_existing_result(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization = await _create_organization(api_client, "API Processing Result", "api-processing-result")
    user = await _create_user(
        api_client,
        "api-processing-result@example.com",
        "API Processing Result",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "api-processing-result@example.com")
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

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=ApiSuccessfulDocumentProcessor(),
        )
        await use_case.execute(UUID(document_payload["id"]))

    response = await api_client.get(
        f"/documents/{document_payload['id']}/processing-result",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["document_id"] == document_payload["id"]
    assert response.json()["status"] == "PROCESSED"
    assert response.json()["extracted_text"] == "API extracted text."
    assert response.json()["summary"] == "API summary."
    assert response.json()["structured_data"] == {"source": "api-test"}


@pytest.mark.anyio
async def test_get_document_processing_result_returns_not_found_for_missing_document(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(
        api_client,
        "Missing Processing Result",
        "missing-processing-result",
    )
    user = await _create_user(
        api_client,
        "missing-processing-result@example.com",
        "Missing Processing Result",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "missing-processing-result@example.com")

    response = await api_client.get(
        f"/documents/{uuid4()}/processing-result",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_document_processing_result_returns_not_found_for_foreign_tenant(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    owner_organization = await _create_organization(
        api_client,
        "Owner Result Org",
        "owner-result-org",
    )
    foreign_organization = await _create_organization(
        api_client,
        "Foreign Result Org",
        "foreign-result-org",
    )
    owner_user = await _create_user(api_client, "owner-result@example.com", "Owner Result")
    foreign_user = await _create_user(
        api_client,
        "foreign-result@example.com",
        "Foreign Result",
    )
    owner_membership = await _create_membership(
        api_client,
        owner_organization["id"],
        owner_user["id"],
    )
    foreign_membership = await _create_membership(
        api_client,
        foreign_organization["id"],
        foreign_user["id"],
    )
    owner_auth = await _login(api_client, "owner-result@example.com")
    foreign_auth = await _login(api_client, "foreign-result@example.com")
    request_payload = await _create_request(
        api_client,
        owner_membership["id"],
        owner_auth["access_token"],
    )
    document_payload = await _create_document(
        api_client,
        request_payload["id"],
        owner_membership["id"],
        owner_auth["access_token"],
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=ApiSuccessfulDocumentProcessor(),
        )
        await use_case.execute(UUID(document_payload["id"]))

    response = await api_client.get(
        f"/documents/{document_payload['id']}/processing-result",
        headers=_membership_headers(foreign_auth["access_token"], foreign_membership["id"]),
    )

    assert response.status_code == 404
