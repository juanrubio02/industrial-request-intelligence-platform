from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.schemas import (
    AuthenticatedMembershipReadModel,
)
from app.application.auth.authorization import MembershipPermission
from app.application.document_processing_results.schemas import (
    DocumentProcessingResultReadModel,
)
from app.application.document_processing_results.services import (
    GetDocumentProcessingResultByDocumentIdUseCase,
)
from app.application.documents.commands import CreateDocumentCommand
from app.application.documents.commands import EnqueueDocumentProcessingCommand
from app.application.documents.commands import UpdateDocumentVerifiedDataCommand
from app.application.documents.commands import UploadDocumentCommand
from app.application.documents.processing import DocumentProcessingDispatcher
from app.application.documents.schemas import DocumentProcessingEnqueuedReadModel
from app.application.documents.schemas import DocumentReadModel
from app.application.documents.services import (
    CreateDocumentUseCase,
    EnqueueDocumentProcessingUseCase,
    GetDocumentByIdUseCase,
    ListRequestDocumentsUseCase,
    UpdateDocumentVerifiedDataUseCase,
    UploadDocumentUseCase,
)
from app.application.documents.storage import DocumentStorage
from app.infrastructure.database.session import get_db_session
from app.infrastructure.document_processing_results.repositories import (
    SqlAlchemyDocumentProcessingResultRepository,
)
from app.infrastructure.documents.repositories import SqlAlchemyDocumentRepository
from app.infrastructure.organization_memberships.repositories import (
    SqlAlchemyOrganizationMembershipRepository,
)
from app.infrastructure.request_activities.repositories import (
    SqlAlchemyRequestActivityRepository,
)
from app.infrastructure.requests.repositories import SqlAlchemyRequestRepository
from app.interfaces.http.dependencies import get_document_processing_dispatcher
from app.interfaces.http.dependencies import get_current_membership
from app.interfaces.http.dependencies import get_document_storage
from app.interfaces.http.dependencies import require_membership_permission
from app.interfaces.http.schemas.documents import (
    CreateDocumentRequest,
    UpdateDocumentVerifiedDataRequest,
)

router = APIRouter(tags=["documents"])


@router.post(
    "/requests/{request_id}/documents",
    response_model=DocumentReadModel,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    request_id: UUID,
    payload: CreateDocumentRequest,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.CREATE_DOCUMENT)
    ),
) -> DocumentReadModel:
    document_repository = SqlAlchemyDocumentRepository(session=session)
    request_repository = SqlAlchemyRequestRepository(session=session)
    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    activity_repository = SqlAlchemyRequestActivityRepository(session=session)
    use_case = CreateDocumentUseCase(
        document_repository=document_repository,
        request_repository=request_repository,
        organization_membership_repository=membership_repository,
        request_activity_repository=activity_repository,
    )
    command = CreateDocumentCommand(
        request_id=request_id,
        organization_id=current_membership.organization_id,
        uploaded_by_membership_id=current_membership.id,
        original_filename=payload.original_filename,
        storage_key=payload.storage_key,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
    )
    return await use_case.execute(command)


@router.post(
    "/requests/{request_id}/documents/upload",
    response_model=DocumentReadModel,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    request_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    document_storage: DocumentStorage = Depends(get_document_storage),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.UPLOAD_DOCUMENT)
    ),
) -> DocumentReadModel:
    document_repository = SqlAlchemyDocumentRepository(session=session)
    request_repository = SqlAlchemyRequestRepository(session=session)
    membership_repository = SqlAlchemyOrganizationMembershipRepository(session=session)
    activity_repository = SqlAlchemyRequestActivityRepository(session=session)
    create_document_use_case = CreateDocumentUseCase(
        document_repository=document_repository,
        request_repository=request_repository,
        organization_membership_repository=membership_repository,
        request_activity_repository=activity_repository,
    )
    upload_use_case = UploadDocumentUseCase(
        document_storage=document_storage,
        create_document_use_case=create_document_use_case,
    )
    command = UploadDocumentCommand(
        request_id=request_id,
        organization_id=current_membership.organization_id,
        uploaded_by_membership_id=current_membership.id,
        original_filename=file.filename or "",
        content_type=file.content_type,
        content=await file.read(),
    )
    return await upload_use_case.execute(command)


@router.get("/documents/{document_id}", response_model=DocumentReadModel)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        get_current_membership
    ),
) -> DocumentReadModel:
    repository = SqlAlchemyDocumentRepository(session=session)
    use_case = GetDocumentByIdUseCase(document_repository=repository)
    return await use_case.execute(document_id, current_membership.organization_id)


@router.get(
    "/documents/{document_id}/processing-result",
    response_model=DocumentProcessingResultReadModel,
)
async def get_document_processing_result(
    document_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        get_current_membership
    ),
) -> DocumentProcessingResultReadModel:
    document_repository = SqlAlchemyDocumentRepository(session=session)
    document_processing_result_repository = SqlAlchemyDocumentProcessingResultRepository(
        session=session
    )
    use_case = GetDocumentProcessingResultByDocumentIdUseCase(
        document_repository=document_repository,
        document_processing_result_repository=document_processing_result_repository,
    )
    return await use_case.execute(document_id, current_membership.organization_id)


@router.get("/requests/{request_id}/documents", response_model=list[DocumentReadModel])
async def list_request_documents(
    request_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        get_current_membership
    ),
) -> list[DocumentReadModel]:
    document_repository = SqlAlchemyDocumentRepository(session=session)
    request_repository = SqlAlchemyRequestRepository(session=session)
    use_case = ListRequestDocumentsUseCase(
        document_repository=document_repository,
        request_repository=request_repository,
    )
    return await use_case.execute(request_id, current_membership.organization_id)


@router.post(
    "/documents/{document_id}/processing-jobs",
    response_model=DocumentProcessingEnqueuedReadModel,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_document_processing(
    document_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(
        require_membership_permission(MembershipPermission.ENQUEUE_DOCUMENT_PROCESSING)
    ),
    document_processing_dispatcher: DocumentProcessingDispatcher = Depends(
        get_document_processing_dispatcher
    ),
) -> DocumentProcessingEnqueuedReadModel:
    document_repository = SqlAlchemyDocumentRepository(session=session)
    use_case = EnqueueDocumentProcessingUseCase(
        document_repository=document_repository,
        document_processing_dispatcher=document_processing_dispatcher,
    )
    command = EnqueueDocumentProcessingCommand(
        document_id=document_id,
        organization_id=current_membership.organization_id,
    )
    return await use_case.execute(command)


@router.patch(
    "/documents/{document_id}/verified-data",
    response_model=DocumentReadModel,
)
async def update_document_verified_data(
    document_id: UUID,
    payload: UpdateDocumentVerifiedDataRequest,
    session: AsyncSession = Depends(get_db_session),
    current_membership: AuthenticatedMembershipReadModel = Depends(get_current_membership),
) -> DocumentReadModel:
    document_repository = SqlAlchemyDocumentRepository(session=session)
    activity_repository = SqlAlchemyRequestActivityRepository(session=session)
    use_case = UpdateDocumentVerifiedDataUseCase(
        document_repository=document_repository,
        request_activity_repository=activity_repository,
    )
    command = UpdateDocumentVerifiedDataCommand(
        document_id=document_id,
        organization_id=current_membership.organization_id,
        membership_id=current_membership.id,
        verified_structured_data=payload.verified_structured_data,
    )
    return await use_case.execute(command)
