from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.domain.documents.statuses import DocumentProcessingStatus
from app.domain.requests.sources import RequestSource
from app.infrastructure.storage.local import LocalDocumentStorage


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


def _assert_generated_storage_key(storage_key: str, *, suffix: str | None = None) -> None:
    assert storage_key.startswith("documents/")
    assert ".." not in storage_key
    if suffix is not None:
        assert storage_key.endswith(suffix)


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
    title: str = "Need industrial filters",
) -> dict:
    response = await api_client.post(
        "/requests",
        json={
            "title": title,
            "description": "Initial request payload",
            "source": RequestSource.EMAIL.value,
        },
        headers=_membership_headers(access_token, membership_id),
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.anyio
async def test_post_request_documents_creates_document(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Acme Docs", "acme-docs")
    user = await _create_user(api_client, "docs@example.com", "Docs User")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "docs@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "specification.pdf",
            "content_type": "application/pdf",
            "size_bytes": 2048,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    payload = response.json()

    assert response.status_code == 201
    assert payload["request_id"] == request_payload["id"]
    assert payload["organization_id"] == organization["id"]
    assert payload["uploaded_by_membership_id"] == membership["id"]
    assert payload["original_filename"] == "specification.pdf"
    _assert_generated_storage_key(payload["storage_key"], suffix=".pdf")
    assert payload["processing_status"] == DocumentProcessingStatus.PENDING.value


@pytest.mark.anyio
async def test_post_request_documents_upload_stores_file_and_creates_document(
    api_client: AsyncClient,
    local_document_storage: LocalDocumentStorage,
) -> None:
    organization = await _create_organization(api_client, "Upload Docs", "upload-docs")
    user = await _create_user(api_client, "upload-docs@example.com", "Upload Docs")
    membership = await _create_membership(
        api_client,
        organization["id"],
        user["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "upload-docs@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/documents/upload",
        files={"file": ("specification.pdf", b"binary-pdf-content", "application/pdf")},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    payload = response.json()
    stored_path = local_document_storage.base_path / payload["storage_key"]

    assert response.status_code == 201
    assert payload["request_id"] == request_payload["id"]
    assert payload["size_bytes"] == 18
    assert payload["content_type"] == "application/pdf"
    _assert_generated_storage_key(payload["storage_key"], suffix=".pdf")
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"binary-pdf-content"


@pytest.mark.anyio
async def test_get_document_by_id_returns_document(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Nova Docs", "nova-docs")
    user = await _create_user(api_client, "nova-docs@example.com", "Nova Docs")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "nova-docs@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )
    create_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "drawing.dxf",
            "content_type": "application/dxf",
            "size_bytes": 4096,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    document_payload = create_response.json()

    response = await api_client.get(
        f"/documents/{document_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == document_payload["id"]
    _assert_generated_storage_key(response.json()["storage_key"], suffix=".dxf")


@pytest.mark.anyio
async def test_get_document_by_id_rejects_spoofed_membership_context(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Spoof Docs", "spoof-docs")
    owner = await _create_user(api_client, "spoof-docs-owner@example.com", "Spoof Docs Owner")
    intruder = await _create_user(api_client, "spoof-docs-intruder@example.com", "Spoof Docs Intruder")
    owner_membership = await _create_membership(
        api_client,
        organization["id"],
        owner["id"],
        role="OWNER",
    )
    intruder_membership = await _create_membership(
        api_client,
        organization["id"],
        intruder["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "spoof-docs-owner@example.com")
    request_payload = await _create_request(
        api_client,
        owner_membership["id"],
        auth_payload["access_token"],
    )
    create_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "spoofed.pdf",
            "content_type": "application/pdf",
            "size_bytes": 512,
        },
        headers=_membership_headers(auth_payload["access_token"], owner_membership["id"]),
    )

    response = await api_client.get(
        f"/documents/{create_response.json()['id']}",
        headers=_membership_headers(auth_payload["access_token"], intruder_membership["id"]),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Membership context is invalid."


@pytest.mark.anyio
async def test_get_request_documents_returns_request_documents(api_client: AsyncClient) -> None:
    organization = await _create_organization(api_client, "Orbit Docs", "orbit-docs")
    user = await _create_user(api_client, "orbit-docs@example.com", "Orbit Docs")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "orbit-docs@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    first_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "doc-1.pdf",
            "content_type": "application/pdf",
            "size_bytes": 100,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    second_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "doc-2.pdf",
            "content_type": "application/pdf",
            "size_bytes": 200,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    response = await api_client.get(
        f"/requests/{request_payload['id']}/documents",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["request_id"] == request_payload["id"]


@pytest.mark.anyio
async def test_post_request_documents_creates_document_uploaded_activity(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Sigma Docs", "sigma-docs")
    user = await _create_user(api_client, "sigma-docs@example.com", "Sigma Docs")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "sigma-docs@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )
    create_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "offer.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1234,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    document_payload = create_response.json()

    response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 2
    assert activities[1]["type"] == "DOCUMENT_UPLOADED"
    assert activities[1]["payload"]["document_id"] == document_payload["id"]
    assert activities[1]["payload"]["storage_key"] == document_payload["storage_key"]


@pytest.mark.anyio
async def test_get_document_by_id_returns_not_found_for_foreign_tenant(
    api_client: AsyncClient,
) -> None:
    owner_organization = await _create_organization(api_client, "Owner Docs", "owner-docs")
    foreign_organization = await _create_organization(
        api_client,
        "Foreign Docs",
        "foreign-docs",
    )
    owner_user = await _create_user(api_client, "owner-docs@example.com", "Owner Docs")
    foreign_user = await _create_user(api_client, "foreign-docs@example.com", "Foreign Docs")
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
    owner_auth = await _login(api_client, "owner-docs@example.com")
    foreign_auth = await _login(api_client, "foreign-docs@example.com")
    request_payload = await _create_request(
        api_client,
        owner_membership["id"],
        owner_auth["access_token"],
    )
    document_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "foreign-protected.pdf",
            "content_type": "application/pdf",
            "size_bytes": 2048,
        },
        headers=_membership_headers(owner_auth["access_token"], owner_membership["id"]),
    )

    response = await api_client.get(
        f"/documents/{document_response.json()['id']}",
        headers=_membership_headers(foreign_auth["access_token"], foreign_membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_documents_upload_creates_document_uploaded_activity(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Upload Timeline", "upload-timeline")
    user = await _create_user(api_client, "upload-timeline@example.com", "Upload Timeline")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "upload-timeline@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    create_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents/upload",
        files={"file": ("offer.pdf", b"offer-file", "application/pdf")},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    document_payload = create_response.json()

    response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 2
    assert activities[1]["type"] == "DOCUMENT_UPLOADED"
    assert activities[1]["payload"]["document_id"] == document_payload["id"]
    assert activities[1]["payload"]["original_filename"] == "offer.pdf"


@pytest.mark.anyio
async def test_post_request_documents_upload_rejects_empty_file(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Empty Docs", "empty-docs")
    user = await _create_user(api_client, "empty-docs@example.com", "Empty Docs")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "empty-docs@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_post_request_documents_returns_not_found_for_missing_request(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Helix Docs", "helix-docs")
    user = await _create_user(api_client, "helix-docs@example.com", "Helix Docs")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "helix-docs@example.com")

    response = await api_client.post(
        f"/requests/{uuid4()}/documents",
        json={
            "original_filename": "missing-request.pdf",
            "content_type": "application/pdf",
            "size_bytes": 100,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_documents_upload_returns_not_found_for_missing_request(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Upload Missing", "upload-missing")
    user = await _create_user(api_client, "upload-missing@example.com", "Upload Missing")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "upload-missing@example.com")

    response = await api_client.post(
        f"/requests/{uuid4()}/documents/upload",
        files={"file": ("missing.pdf", b"file-content", "application/pdf")},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_documents_returns_401_for_membership_from_other_user(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Atlas Docs", "atlas-docs")
    owner_user = await _create_user(api_client, "atlas-owner@example.com", "Atlas Owner")
    await _create_user(api_client, "atlas-actor@example.com", "Atlas Actor")
    owner_membership = await _create_membership(api_client, organization["id"], owner_user["id"])
    actor_auth = await _login(api_client, "atlas-actor@example.com")
    owner_auth = await _login(api_client, "atlas-owner@example.com")
    request_payload = await _create_request(
        api_client,
        owner_membership["id"],
        owner_auth["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "forbidden.pdf",
            "content_type": "application/pdf",
            "size_bytes": 100,
        },
        headers=_membership_headers(actor_auth["access_token"], owner_membership["id"]),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Membership context is invalid."


@pytest.mark.anyio
async def test_post_request_documents_upload_returns_conflict_for_membership_from_other_organization(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Upload Alpha", "upload-alpha")
    other_organization = await _create_organization(api_client, "Upload Beta", "upload-beta")
    user = await _create_user(api_client, "upload-cross@example.com", "Upload Cross")
    request_membership = await _create_membership(api_client, organization["id"], user["id"])
    upload_membership = await _create_membership(api_client, other_organization["id"], user["id"])
    auth_payload = await _login(api_client, "upload-cross@example.com")
    request_payload = await _create_request(
        api_client,
        request_membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/documents/upload",
        files={"file": ("cross-org.pdf", b"file-content", "application/pdf")},
        headers=_membership_headers(auth_payload["access_token"], upload_membership["id"]),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "The provided request does not belong to the provided organization."
    )


@pytest.mark.anyio
async def test_patch_document_verified_data_updates_document_and_creates_activity(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Verify Docs", "verify-docs")
    user = await _create_user(api_client, "verify-docs@example.com", "Verify Docs")
    membership = await _create_membership(
        api_client,
        organization["id"],
        user["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "verify-docs@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )
    create_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "rfq.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1234,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )
    document_payload = create_response.json()

    response = await api_client.patch(
        f"/documents/{document_payload['id']}/verified-data",
        json={
            "verified_structured_data": {
                "material": "Stainless steel",
                "requested_quantity": "24",
                "delivery_deadline": "2026-04-30",
                "rfq_number": "RFQ-2026-001",
            }
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 200
    assert response.json()["verified_structured_data"] == {
        "material": "Stainless steel",
        "requested_quantity": "24",
        "delivery_deadline": "2026-04-30",
        "rfq_number": "RFQ-2026-001",
    }

    activities_response = await api_client.get(
        f"/requests/{request_payload['id']}/activities",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert activities_response.status_code == 200
    activities = activities_response.json()
    assert activities[-1]["type"] == "DOCUMENT_VERIFIED_DATA_UPDATED"
    assert activities[-1]["payload"]["document_id"] == document_payload["id"]
    assert activities[-1]["payload"]["verified_structured_data"]["material"] == "Stainless steel"


@pytest.mark.anyio
async def test_patch_document_verified_data_requires_authentication(
    api_client: AsyncClient,
) -> None:
    response = await api_client.patch(
        f"/documents/{uuid4()}/verified-data",
        json={"verified_structured_data": {"material": "Steel"}},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_patch_document_verified_data_returns_not_found_for_foreign_tenant(
    api_client: AsyncClient,
) -> None:
    owner_organization = await _create_organization(api_client, "Owner Verify", "owner-verify")
    foreign_organization = await _create_organization(
        api_client,
        "Foreign Verify",
        "foreign-verify",
    )
    owner_user = await _create_user(api_client, "owner-verify@example.com", "Owner Verify")
    foreign_user = await _create_user(
        api_client,
        "foreign-verify@example.com",
        "Foreign Verify",
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
    owner_auth = await _login(api_client, "owner-verify@example.com")
    foreign_auth = await _login(api_client, "foreign-verify@example.com")
    request_payload = await _create_request(
        api_client,
        owner_membership["id"],
        owner_auth["access_token"],
    )
    create_response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "tenant-protected.pdf",
            "content_type": "application/pdf",
            "size_bytes": 200,
        },
        headers=_membership_headers(owner_auth["access_token"], owner_membership["id"]),
    )
    document_payload = create_response.json()

    response = await api_client.patch(
        f"/documents/{document_payload['id']}/verified-data",
        json={"verified_structured_data": {"material": "Titanium"}},
        headers=_membership_headers(foreign_auth["access_token"], foreign_membership["id"]),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_post_request_documents_rejects_client_controlled_storage_key(
    api_client: AsyncClient,
) -> None:
    organization = await _create_organization(api_client, "Path Guard", "path-guard")
    user = await _create_user(api_client, "path-guard@example.com", "Path Guard")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "path-guard@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/documents",
        json={
            "original_filename": "rfq.pdf",
            "storage_key": "../../etc/passwd",
            "content_type": "application/pdf",
            "size_bytes": 1024,
        },
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_post_request_documents_upload_sanitizes_malicious_filename(
    api_client: AsyncClient,
    local_document_storage: LocalDocumentStorage,
) -> None:
    organization = await _create_organization(api_client, "Filename Guard", "filename-guard")
    user = await _create_user(api_client, "filename-guard@example.com", "Filename Guard")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "filename-guard@example.com")
    request_payload = await _create_request(
        api_client,
        membership["id"],
        auth_payload["access_token"],
    )

    response = await api_client.post(
        f"/requests/{request_payload['id']}/documents/upload",
        files={"file": ("../../etc/passwd", b"safe-content", "text/plain")},
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    payload = response.json()
    stored_path = local_document_storage.base_path / payload["storage_key"]

    assert response.status_code == 201
    _assert_generated_storage_key(payload["storage_key"])
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"safe-content"
