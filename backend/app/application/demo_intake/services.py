from uuid import UUID

import fitz

from app.application.common.pagination import PaginatedResult, PaginationParams
from app.application.demo_intake.exceptions import DemoIntakeScenarioNotFoundError
from app.application.demo_intake.schemas import (
    DemoIntakeRunResultReadModel,
    DemoIntakeScenarioReadModel,
)
from app.application.demo_intake.scenarios import (
    DemoIntakeScenario,
    DemoScenarioAttachment,
    load_demo_intake_scenarios,
)
from app.application.documents.commands import EnqueueDocumentProcessingCommand
from app.application.documents.commands import UploadDocumentCommand
from app.application.documents.services import (
    EnqueueDocumentProcessingUseCase,
    UploadDocumentUseCase,
)
from app.application.request_comments.commands import CreateRequestCommentCommand
from app.application.request_comments.services import CreateRequestCommentUseCase
from app.application.requests.commands import CreateRequestCommand
from app.application.requests.services import CreateRequestUseCase


class ListDemoIntakeScenariosUseCase:
    def execute(self, pagination: PaginationParams) -> PaginatedResult[DemoIntakeScenarioReadModel]:
        scenarios = [
            DemoIntakeScenarioReadModel(
                key=scenario.key,
                title=scenario.title,
                source=scenario.source,
                sender=scenario.sender,
                expected_document_type=scenario.expected_document_type,
                attachments=len(scenario.attachments),
                description=scenario.description,
            )
            for scenario in load_demo_intake_scenarios().values()
        ]
        items = scenarios[pagination.offset : pagination.offset + pagination.limit]
        return PaginatedResult(
            items=items,
            total=len(scenarios),
            limit=pagination.limit,
            offset=pagination.offset,
        )


class RunDemoIntakeScenarioUseCase:
    def __init__(
        self,
        create_request_use_case: CreateRequestUseCase,
        upload_document_use_case: UploadDocumentUseCase,
        enqueue_document_processing_use_case: EnqueueDocumentProcessingUseCase,
        create_request_comment_use_case: CreateRequestCommentUseCase,
    ) -> None:
        self._create_request_use_case = create_request_use_case
        self._upload_document_use_case = upload_document_use_case
        self._enqueue_document_processing_use_case = enqueue_document_processing_use_case
        self._create_request_comment_use_case = create_request_comment_use_case

    async def execute(
        self,
        *,
        scenario_key: str,
        organization_id: UUID,
        membership_id: UUID,
    ) -> DemoIntakeRunResultReadModel:
        scenario = load_demo_intake_scenarios().get(scenario_key)
        if scenario is None:
            raise DemoIntakeScenarioNotFoundError(
                f"Demo intake scenario '{scenario_key}' was not found."
            )

        request = await self._create_request_use_case.execute(
            organization_id,
            CreateRequestCommand(
                title=scenario.subject,
                description=self._build_request_description(scenario),
                source=scenario.source,
                created_by_membership_id=membership_id,
            )
        )

        document_ids: list[UUID] = []
        for attachment in scenario.attachments:
            content = self._render_attachment(attachment)
            document = await self._upload_document_use_case.execute(
                UploadDocumentCommand(
                    request_id=request.id,
                    organization_id=organization_id,
                    uploaded_by_membership_id=membership_id,
                    original_filename=attachment.filename,
                    content_type=attachment.content_type,
                    content=content,
                )
            )
            document_ids.append(document.id)
            await self._enqueue_document_processing_use_case.execute(
                EnqueueDocumentProcessingCommand(
                    document_id=document.id,
                    organization_id=organization_id,
                )
            )

        if scenario.initial_comment:
            await self._create_request_comment_use_case.execute(
                request.id,
                CreateRequestCommentCommand(
                    organization_id=organization_id,
                    membership_id=membership_id,
                    body=scenario.initial_comment,
                ),
            )

        return DemoIntakeRunResultReadModel(
            request_id=request.id,
            document_ids=document_ids,
            scenario_key=scenario.key,
        )

    @staticmethod
    def _build_request_description(scenario: DemoIntakeScenario) -> str:
        return (
            f"Sender: {scenario.sender}\n"
            f"Subject: {scenario.subject}\n\n"
            f"{scenario.body}"
        )

    def _render_attachment(self, attachment: DemoScenarioAttachment) -> bytes:
        if attachment.template_kind == "SCANNED_PDF":
            return self._build_scanned_pdf(attachment.content)

        return attachment.content.encode("utf-8")

    @staticmethod
    def _build_scanned_pdf(text: str) -> bytes:
        source_pdf = fitz.open()
        source_page = source_pdf.new_page(width=595, height=842)
        source_page.insert_textbox(
            fitz.Rect(48, 72, 547, 770),
            text,
            fontsize=14,
            lineheight=1.4,
        )
        pixmap = source_pdf[0].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
        png_bytes = pixmap.tobytes("png")
        source_pdf.close()

        scanned_pdf = fitz.open()
        scanned_page = scanned_pdf.new_page(width=595, height=842)
        scanned_page.insert_image(scanned_page.rect, stream=png_bytes)
        output = scanned_pdf.tobytes()
        scanned_pdf.close()
        return output
