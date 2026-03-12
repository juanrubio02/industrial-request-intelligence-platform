from io import BytesIO
from uuid import UUID

import fitz
import pytest
from httpx import AsyncClient
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.document_processing_results.services import (
    GetDocumentProcessingResultByDocumentIdUseCase,
)
from app.application.documents.processing import DocumentProcessingDispatcher
from app.application.documents.services import ProcessDocumentUseCase
from app.domain.document_processing_results.document_types import (
    DocumentDetectedType,
)
from app.domain.documents.statuses import DocumentProcessingStatus
from app.domain.requests.sources import RequestSource
from app.infrastructure.document_processing.ocr import PdfOcrExtractor
from app.infrastructure.document_processing.processor import StorageBackedDocumentProcessor
from app.infrastructure.document_processing_results.repositories import (
    SqlAlchemyDocumentProcessingResultRepository,
)
from app.infrastructure.documents.repositories import SqlAlchemyDocumentRepository


class RecordingDocumentProcessingDispatcher(DocumentProcessingDispatcher):
    def __init__(self) -> None:
        self.enqueued_document_ids: list[UUID] = []

    async def enqueue(self, document_id: UUID) -> None:
        self.enqueued_document_ids.append(document_id)


class FailingPdfOcrExtractor(PdfOcrExtractor):
    def extract_text(self, file_bytes: bytes) -> str:
        raise RuntimeError("OCR processing failed for the PDF.")


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
    *,
    filename: str = "specification.txt",
    content: bytes = b"Industrial request text content.",
    content_type: str = "text/plain",
) -> dict:
    response = await api_client.post(
        f"/requests/{request_id}/documents/upload",
        files={"file": (filename, content, content_type)},
        headers=_membership_headers(access_token, membership_id),
    )
    assert response.status_code == 201
    return response.json()


def _build_embedded_text_pdf_bytes(text: str) -> bytes:
    stream = f"BT\n/F1 12 Tf\n72 72 Td\n({text}) Tj\nET".encode("utf-8")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
            b"endobj\n"
        ),
        (
            b"4 0 obj\n"
            + f"<< /Length {len(stream)} >>\nstream\n".encode("utf-8")
            + stream
            + b"\nendstream\nendobj\n"
        ),
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("utf-8"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("utf-8"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("utf-8")
    )
    return bytes(pdf)


def _build_scanned_pdf_bytes(text: str) -> bytes:
    image = Image.new("RGB", (1200, 500), "white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 88)
    except Exception:
        font = ImageFont.load_default()

    draw.text((60, 180), text, fill="black", font=font)

    image_buffer = BytesIO()
    image.save(image_buffer, format="PNG")

    document = fitz.open()
    page = document.new_page(width=1200, height=500)
    page.insert_image(page.rect, stream=image_buffer.getvalue())
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


@pytest.mark.anyio
async def test_process_document_use_case_classifies_quote_request(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(
        api_client, "Processing Success", "processing-success"
    )
    user = await _create_user(api_client, "processing-success@example.com", "Processing Success")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-success@example.com")
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
        filename="rfq-request.txt",
        content=(
            b"Request for quotation for stainless steel valves required for line A. "
            b"Delivery is needed before June 30. Please include pricing and lead time."
        ),
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        result = await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    response = await api_client.get(
        f"/documents/{document_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert result.processing_status == DocumentProcessingStatus.PROCESSED
    assert response.status_code == 200
    assert response.json()["processing_status"] == DocumentProcessingStatus.PROCESSED.value
    assert processing_result.document_id == UUID(document_payload["id"])
    assert processing_result.status == "PROCESSED"
    assert (
        processing_result.extracted_text
        == "Request for quotation for stainless steel valves required for line A. "
        "Delivery is needed before June 30. Please include pricing and lead time."
    )
    assert (
        processing_result.summary
        == "Request for quotation for stainless steel valves required for line A. "
        "Delivery is needed before June 30."
    )
    assert processing_result.detected_document_type == DocumentDetectedType.QUOTE_REQUEST
    assert processing_result.error_message is None
    assert processing_result.structured_data["extracted_fields"] == {
        "delivery_deadline": "June 30",
        "extraction_context": DocumentDetectedType.QUOTE_REQUEST.value,
    }


@pytest.mark.anyio
async def test_process_document_use_case_classifies_technical_spec(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(
        api_client, "Processing Markdown", "processing-markdown"
    )
    user = await _create_user(
        api_client,
        "processing-markdown@example.com",
        "Processing Markdown",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-markdown@example.com")
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
        filename="pump_spec.md",
        content=b"# Technical Specification\n\nOperating conditions and material grade.",
        content_type="text/markdown",
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        result = await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    response = await api_client.get(
        f"/documents/{document_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert result.processing_status == DocumentProcessingStatus.PROCESSED
    assert response.status_code == 200
    assert response.json()["processing_status"] == DocumentProcessingStatus.PROCESSED.value
    assert processing_result.document_id == UUID(document_payload["id"])
    assert processing_result.status == "PROCESSED"
    assert (
        processing_result.extracted_text
        == "# Technical Specification\n\nOperating conditions and material grade."
    )
    assert processing_result.summary is None
    assert processing_result.detected_document_type == DocumentDetectedType.TECHNICAL_SPEC
    assert processing_result.error_message is None


@pytest.mark.anyio
async def test_process_document_use_case_classifies_purchase_order(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(
        api_client, "Processing Purchase Order", "processing-purchase-order"
    )
    user = await _create_user(
        api_client,
        "processing-purchase-order@example.com",
        "Processing Purchase Order",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-purchase-order@example.com")
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
        filename="purchase_order.txt",
        content=b"Purchase Order\nPO Number: 12345\nShip To: Acme Plant",
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        result = await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    response = await api_client.get(
        f"/documents/{document_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert result.processing_status == DocumentProcessingStatus.PROCESSED
    assert response.status_code == 200
    assert response.json()["processing_status"] == DocumentProcessingStatus.PROCESSED.value
    assert processing_result.status == "PROCESSED"
    assert "Purchase Order" in processing_result.extracted_text
    assert processing_result.summary is None
    assert processing_result.detected_document_type == DocumentDetectedType.PURCHASE_ORDER
    assert processing_result.error_message is None
    assert processing_result.structured_data["extracted_fields"] == {
        "extraction_context": DocumentDetectedType.PURCHASE_ORDER.value,
        "purchase_order_number": "12345",
    }


@pytest.mark.anyio
async def test_process_document_use_case_extracts_structured_fields_from_rfq_text(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(
        api_client, "Structured RFQ", "structured-rfq"
    )
    user = await _create_user(api_client, "structured-rfq@example.com", "Structured RFQ")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "structured-rfq@example.com")
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
        filename="rfq-structured.txt",
        content=(
            b"Request for quotation\n"
            b"RFQ Number: RFQ-2026-001\n"
            b"Document Reference: DOC-778\n"
            b"Requested Quantity: 25 units\n"
            b"Material: Stainless Steel 316L\n"
            b"Delivery Deadline: 2026-06-30\n"
        ),
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    assert processing_result.structured_data["extracted_fields"] == {
        "document_reference": "DOC-778",
        "requested_quantity": "25 units",
        "material": "Stainless Steel 316L",
        "delivery_deadline": "2026-06-30",
        "rfq_number": "RFQ-2026-001",
        "extraction_context": DocumentDetectedType.QUOTE_REQUEST.value,
    }


@pytest.mark.anyio
async def test_process_document_use_case_classifies_drawing_from_pdf(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(api_client, "Processing PDF", "processing-pdf")
    user = await _create_user(api_client, "processing-pdf@example.com", "Processing PDF")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-pdf@example.com")
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
        filename="pump_drawing.pdf",
        content=_build_embedded_text_pdf_bytes("General Arrangement Drawing\nDrawing No 42"),
        content_type="application/pdf",
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        result = await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    response = await api_client.get(
        f"/documents/{document_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert result.processing_status == DocumentProcessingStatus.PROCESSED
    assert response.status_code == 200
    assert response.json()["processing_status"] == DocumentProcessingStatus.PROCESSED.value
    assert processing_result.status == "PROCESSED"
    assert "General Arrangement Drawing" in processing_result.extracted_text
    assert processing_result.summary is None
    assert processing_result.detected_document_type == DocumentDetectedType.DRAWING
    assert processing_result.error_message is None


@pytest.mark.anyio
async def test_process_document_use_case_falls_back_to_ocr_for_scanned_pdf(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(api_client, "Processing OCR", "processing-ocr")
    user = await _create_user(api_client, "processing-ocr@example.com", "Processing OCR")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-ocr@example.com")
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
        filename="scanned-rfq.pdf",
        content=_build_scanned_pdf_bytes("SCANNED RFQ 123"),
        content_type="application/pdf",
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        result = await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    assert result.processing_status == DocumentProcessingStatus.PROCESSED
    assert processing_result.status == "PROCESSED"
    assert processing_result.extracted_text is not None
    assert "SCANNED" in processing_result.extracted_text.upper()
    assert "RFQ" in processing_result.extracted_text.upper()
    assert processing_result.structured_data["ocr_used"] is True
    assert processing_result.structured_data["text_extraction_strategy"] == "OCR"
    assert processing_result.detected_document_type == DocumentDetectedType.QUOTE_REQUEST
    assert processing_result.error_message is None


@pytest.mark.anyio
async def test_process_document_use_case_falls_back_to_other_for_ambiguous_document(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(
        api_client, "Processing Other", "processing-other"
    )
    user = await _create_user(api_client, "processing-other@example.com", "Processing Other")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-other@example.com")
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
        filename="notes.txt",
        content=b"Meeting notes about next week follow-up.",
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        result = await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    response = await api_client.get(
        f"/documents/{document_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert result.processing_status == DocumentProcessingStatus.PROCESSED
    assert response.status_code == 200
    assert response.json()["processing_status"] == DocumentProcessingStatus.PROCESSED.value
    assert processing_result.status == "PROCESSED"
    assert processing_result.summary is None
    assert processing_result.detected_document_type == DocumentDetectedType.OTHER
    assert processing_result.structured_data["extracted_fields"] == {
        "extraction_context": DocumentDetectedType.OTHER.value
    }
    assert processing_result.error_message is None


@pytest.mark.anyio
async def test_process_document_use_case_extracts_partial_structured_data_when_signals_are_sparse(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(
        api_client, "Structured Partial", "structured-partial"
    )
    user = await _create_user(
        api_client,
        "structured-partial@example.com",
        "Structured Partial",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "structured-partial@example.com")
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
        filename="partial-po.txt",
        content=b"Purchase Order\nPO Number: PO-7788\nPlease confirm receipt.",
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    assert processing_result.structured_data["extracted_fields"] == {
        "purchase_order_number": "PO-7788",
        "extraction_context": DocumentDetectedType.PURCHASE_ORDER.value,
    }


@pytest.mark.anyio
async def test_process_document_use_case_persists_failed_result_when_ocr_fails(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(
        api_client, "Processing OCR Failed", "processing-ocr-failed"
    )
    user = await _create_user(
        api_client,
        "processing-ocr-failed@example.com",
        "Processing OCR Failed",
    )
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-ocr-failed@example.com")
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
        filename="scanned-failure.pdf",
        content=_build_scanned_pdf_bytes("SCANNED FAILURE"),
        content_type="application/pdf",
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage,
                pdf_ocr_extractor=FailingPdfOcrExtractor(),
            ),
        )
        result = await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    assert result.processing_status == DocumentProcessingStatus.FAILED
    assert processing_result.status == "FAILED"
    assert processing_result.extracted_text is None
    assert processing_result.error_message == "OCR processing failed for the PDF."


@pytest.mark.anyio
async def test_process_document_use_case_transitions_pending_to_failed_for_invalid_pdf(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    local_document_storage,
) -> None:
    organization = await _create_organization(
        api_client, "Processing Failed", "processing-failed"
    )
    user = await _create_user(api_client, "processing-failed@example.com", "Processing Failed")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "processing-failed@example.com")
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
        filename="specification.pdf",
        content=b"%PDF-1.4 invalid pdf payload",
        content_type="application/pdf",
    )

    async with session_factory() as session:
        use_case = ProcessDocumentUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
            document_processor=StorageBackedDocumentProcessor(
                document_storage=local_document_storage
            ),
        )
        result = await use_case.execute(UUID(document_payload["id"]))
        processing_result = await GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=SqlAlchemyDocumentRepository(session=session),
            document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
                session=session
            ),
        ).execute(UUID(document_payload["id"]), UUID(organization["id"]))

    response = await api_client.get(
        f"/documents/{document_payload['id']}",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert result.processing_status == DocumentProcessingStatus.FAILED
    assert response.status_code == 200
    assert response.json()["processing_status"] == DocumentProcessingStatus.FAILED.value
    assert processing_result.document_id == UUID(document_payload["id"])
    assert processing_result.status == "FAILED"
    assert processing_result.summary is None
    assert processing_result.error_message == "PDF file could not be read."


@pytest.fixture
def recording_document_processing_dispatcher() -> RecordingDocumentProcessingDispatcher:
    return RecordingDocumentProcessingDispatcher()


@pytest.fixture
def document_processing_dispatcher_override(
    recording_document_processing_dispatcher: RecordingDocumentProcessingDispatcher,
) -> RecordingDocumentProcessingDispatcher:
    return recording_document_processing_dispatcher


@pytest.mark.anyio
async def test_post_document_processing_jobs_enqueues_document(
    api_client: AsyncClient,
    recording_document_processing_dispatcher: RecordingDocumentProcessingDispatcher,
) -> None:
    organization = await _create_organization(api_client, "Enqueue Docs", "enqueue-docs")
    user = await _create_user(api_client, "enqueue-docs@example.com", "Enqueue Docs")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "enqueue-docs@example.com")
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

    response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 202
    assert response.json()["document_id"] == document_payload["id"]
    assert response.json()["processing_status"] == DocumentProcessingStatus.PENDING.value
    assert recording_document_processing_dispatcher.enqueued_document_ids == [
        UUID(document_payload["id"])
    ]


@pytest.mark.anyio
async def test_post_document_processing_jobs_allows_owner_role(
    api_client: AsyncClient,
    recording_document_processing_dispatcher: RecordingDocumentProcessingDispatcher,
) -> None:
    organization = await _create_organization(api_client, "Owner Enqueue Docs", "owner-enqueue-docs")
    user = await _create_user(api_client, "owner-enqueue@example.com", "Owner Enqueue")
    membership = await _create_membership(
        api_client,
        organization["id"],
        user["id"],
        role="OWNER",
    )
    auth_payload = await _login(api_client, "owner-enqueue@example.com")
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

    response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 202
    assert response.json()["document_id"] == document_payload["id"]
    assert recording_document_processing_dispatcher.enqueued_document_ids == [
        UUID(document_payload["id"])
    ]


@pytest.mark.anyio
async def test_post_document_processing_jobs_returns_403_for_member_role(
    api_client: AsyncClient,
    recording_document_processing_dispatcher: RecordingDocumentProcessingDispatcher,
) -> None:
    organization = await _create_organization(api_client, "Member Enqueue Docs", "member-enqueue-docs")
    user = await _create_user(api_client, "member-enqueue@example.com", "Member Enqueue")
    membership = await _create_membership(
        api_client,
        organization["id"],
        user["id"],
        role="MEMBER",
    )
    auth_payload = await _login(api_client, "member-enqueue@example.com")
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

    response = await api_client.post(
        f"/documents/{document_payload['id']}/processing-jobs",
        headers=_membership_headers(auth_payload["access_token"], membership["id"]),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Membership role 'MEMBER' is not allowed to perform 'ENQUEUE_DOCUMENT_PROCESSING'."
    )
    assert recording_document_processing_dispatcher.enqueued_document_ids == []


@pytest.mark.anyio
async def test_post_document_processing_jobs_returns_401_without_authentication(
    api_client: AsyncClient,
    recording_document_processing_dispatcher: RecordingDocumentProcessingDispatcher,
) -> None:
    organization = await _create_organization(api_client, "Enqueue Docs Auth", "enqueue-docs-auth")
    user = await _create_user(api_client, "enqueue-docs-auth@example.com", "Enqueue Docs Auth")
    membership = await _create_membership(api_client, organization["id"], user["id"])
    auth_payload = await _login(api_client, "enqueue-docs-auth@example.com")
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

    response = await api_client.post(f"/documents/{document_payload['id']}/processing-jobs")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token."
    assert recording_document_processing_dispatcher.enqueued_document_ids == []
