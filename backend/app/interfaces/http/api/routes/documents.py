from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.application.auth.authorization import MembershipPermission
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.application.document_processing_results.schemas import (
    DocumentProcessingResultReadModel,
)
from app.application.documents.commands import (
    CreateDocumentCommand,
    EnqueueDocumentProcessingCommand,
    UpdateDocumentVerifiedDataCommand,
    UploadDocumentCommand,
)
from app.application.documents.schemas import (
    DocumentProcessingEnqueuedReadModel,
    DocumentReadModel,
)
from app.interfaces.http.dependencies import (
    get_service_factory,
    require_membership_permission,
)
from app.interfaces.http.pagination import Pagination
from app.interfaces.http.responses import paginated_response, success_response
from app.interfaces.http.schemas.common import ApiSuccessResponse, PaginatedResponse
from app.interfaces.http.schemas.documents import (
    CreateDocumentRequest,
    UpdateDocumentVerifiedDataRequest,
)
from app.interfaces.http.services import ServiceFactory

router = APIRouter(tags=["documents"])


@router.post(
    "/requests/{request_id}/documents",
    response_model=ApiSuccessResponse[DocumentReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    request_id: UUID,
    payload: CreateDocumentRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_DOCUMENT)
    ),
) -> ApiSuccessResponse[DocumentReadModel]:
    return success_response(
        await services.create_document_use_case.execute(
            CreateDocumentCommand(
                request_id=request_id,
                organization_id=current_membership.organization_id,
                uploaded_by_membership_id=current_membership.id,
                original_filename=payload.original_filename,
                content_type=payload.content_type,
                size_bytes=payload.size_bytes,
            )
        )
    )


@router.post(
    "/requests/{request_id}/documents/upload",
    response_model=ApiSuccessResponse[DocumentReadModel],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    request_id: UUID,
    file: UploadFile = File(...),
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.UPLOAD_DOCUMENT)
    ),
) -> ApiSuccessResponse[DocumentReadModel]:
    return success_response(
        await services.upload_document_use_case.execute(
            UploadDocumentCommand(
                request_id=request_id,
                organization_id=current_membership.organization_id,
                uploaded_by_membership_id=current_membership.id,
                original_filename=file.filename or "",
                content_type=file.content_type,
                content=await file.read(),
            )
        )
    )


@router.get(
    "/documents/{document_id}",
    response_model=ApiSuccessResponse[DocumentReadModel],
)
async def get_document(
    document_id: UUID,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_REQUESTS)
    ),
) -> ApiSuccessResponse[DocumentReadModel]:
    return success_response(
        await services.get_document_by_id_use_case.execute(
            document_id,
            current_membership.organization_id,
        )
    )


@router.get(
    "/documents/{document_id}/processing-result",
    response_model=ApiSuccessResponse[DocumentProcessingResultReadModel],
)
async def get_document_processing_result(
    document_id: UUID,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_REQUESTS)
    ),
) -> ApiSuccessResponse[DocumentProcessingResultReadModel]:
    return success_response(
        await services.get_document_processing_result_by_document_id_use_case.execute(
            document_id,
            current_membership.organization_id,
        )
    )


@router.get(
    "/requests/{request_id}/documents",
    response_model=PaginatedResponse[DocumentReadModel],
)
async def list_request_documents(
    request_id: UUID,
    pagination: Pagination,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.VIEW_REQUESTS)
    ),
) -> PaginatedResponse[DocumentReadModel]:
    result = await services.list_request_documents_use_case.execute(
        request_id,
        current_membership.organization_id,
        pagination,
    )
    return paginated_response(result)


@router.post(
    "/documents/{document_id}/processing-jobs",
    response_model=ApiSuccessResponse[DocumentProcessingEnqueuedReadModel],
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_document_processing(
    document_id: UUID,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.ENQUEUE_DOCUMENT_PROCESSING)
    ),
) -> ApiSuccessResponse[DocumentProcessingEnqueuedReadModel]:
    return success_response(
        await services.enqueue_document_processing_use_case.execute(
            EnqueueDocumentProcessingCommand(
                document_id=document_id,
                organization_id=current_membership.organization_id,
            )
        )
    )


@router.patch(
    "/documents/{document_id}/verified-data",
    response_model=ApiSuccessResponse[DocumentReadModel],
)
async def update_document_verified_data(
    document_id: UUID,
    payload: UpdateDocumentVerifiedDataRequest,
    services: ServiceFactory = Depends(get_service_factory),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.UPDATE_VERIFIED_DOCUMENT_DATA)
    ),
) -> ApiSuccessResponse[DocumentReadModel]:
    return success_response(
        await services.update_document_verified_data_use_case.execute(
            UpdateDocumentVerifiedDataCommand(
                document_id=document_id,
                organization_id=current_membership.organization_id,
                membership_id=current_membership.id,
                verified_structured_data=payload.verified_structured_data,
            )
        )
    )
