from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.pipeline_analytics_service import PipelineAnalyticsService
from app.application.auth.authorization import MembershipAuthorizationService
from app.application.auth.password import PasswordHasher
from app.application.auth.services import (
    BuildAuthenticatedSessionUserUseCase,
    GetAuthenticatedMembershipUseCase,
    GetAuthenticatedUserUseCase,
    ListAuthenticatedMembershipsUseCase,
    LoginUserUseCase,
    LogoutSessionUseCase,
    RefreshSessionUseCase,
)
from app.application.auth.tokens import TokenService
from app.infrastructure.auth.repositories import SqlAlchemyAuthSessionRepository
from app.application.demo_intake.services import (
    ListDemoIntakeScenariosUseCase,
    RunDemoIntakeScenarioUseCase,
)
from app.application.document_processing_results.services import (
    GetDocumentProcessingResultByDocumentIdUseCase,
)
from app.application.documents.processing import DocumentProcessingDispatcher
from app.application.documents.services import (
    CreateDocumentUseCase,
    EnqueueDocumentProcessingUseCase,
    GetDocumentByIdUseCase,
    ListRequestDocumentsUseCase,
    ProcessDocumentUseCase,
    UpdateDocumentVerifiedDataUseCase,
    UploadDocumentUseCase,
)
from app.application.documents.storage import DocumentStorage
from app.application.health.service import HealthService
from app.application.organization_memberships.services import (
    CreateOrganizationMembershipUseCase,
    GetOrganizationMembershipUseCase,
    ListOrganizationMembershipsUseCase,
    UpdateOrganizationMembershipRoleUseCase,
    UpdateOrganizationMembershipStatusUseCase,
)
from app.application.organizations.services import (
    CreateOrganizationUseCase,
    GetOrganizationByIdUseCase,
)
from app.application.request_comments.services import (
    CreateRequestCommentUseCase,
    ListRequestCommentsUseCase,
)
from app.application.requests.services import (
    AssignRequestUseCase,
    CreateRequestUseCase,
    GetRequestByIdUseCase,
    ListRequestActivitiesUseCase,
    ListRequestsUseCase,
    TransitionRequestStatusUseCase,
    UpdateRequestUseCase,
)
from app.application.users.services import CreateUserUseCase
from app.core.settings import Settings
from app.infrastructure.analytics.repositories import SqlAlchemyPipelineAnalyticsRepository
from app.infrastructure.customers.repositories import SqlAlchemyCustomerRepository
from app.infrastructure.document_processing.processor import StorageBackedDocumentProcessor
from app.infrastructure.document_processing.worker import DocumentProcessingWorker
from app.infrastructure.document_processing_results.repositories import (
    SqlAlchemyDocumentProcessingResultRepository,
)
from app.infrastructure.documents.repositories import SqlAlchemyDocumentRepository
from app.infrastructure.organization_memberships.repositories import (
    SqlAlchemyOrganizationMembershipRepository,
)
from app.infrastructure.organizations.repositories import SqlAlchemyOrganizationRepository
from app.infrastructure.request_activities.repositories import (
    SqlAlchemyRequestActivityRepository,
)
from app.infrastructure.request_comments.repositories import SqlAlchemyRequestCommentRepository
from app.infrastructure.request_status_history.repositories import (
    SqlAlchemyRequestStatusHistoryRepository,
)
from app.infrastructure.requests.repositories import SqlAlchemyRequestRepository
from app.infrastructure.users.repositories import SqlAlchemyUserRepository


@dataclass
class ServiceFactory:
    session: AsyncSession
    settings: Settings
    password_hasher: PasswordHasher
    token_service: TokenService
    document_storage: DocumentStorage
    document_processing_dispatcher: DocumentProcessingDispatcher

    @cached_property
    def user_repository(self) -> SqlAlchemyUserRepository:
        return SqlAlchemyUserRepository(session=self.session)

    @cached_property
    def auth_session_repository(self) -> SqlAlchemyAuthSessionRepository:
        return SqlAlchemyAuthSessionRepository(session=self.session)

    @cached_property
    def organization_repository(self) -> SqlAlchemyOrganizationRepository:
        return SqlAlchemyOrganizationRepository(session=self.session)

    @cached_property
    def organization_membership_repository(self) -> SqlAlchemyOrganizationMembershipRepository:
        return SqlAlchemyOrganizationMembershipRepository(session=self.session)

    @cached_property
    def request_repository(self) -> SqlAlchemyRequestRepository:
        return SqlAlchemyRequestRepository(session=self.session)

    @cached_property
    def request_activity_repository(self) -> SqlAlchemyRequestActivityRepository:
        return SqlAlchemyRequestActivityRepository(session=self.session)

    @cached_property
    def request_comment_repository(self) -> SqlAlchemyRequestCommentRepository:
        return SqlAlchemyRequestCommentRepository(session=self.session)

    @cached_property
    def request_status_history_repository(self) -> SqlAlchemyRequestStatusHistoryRepository:
        return SqlAlchemyRequestStatusHistoryRepository(session=self.session)

    @cached_property
    def customer_repository(self) -> SqlAlchemyCustomerRepository:
        return SqlAlchemyCustomerRepository(session=self.session)

    @cached_property
    def document_repository(self) -> SqlAlchemyDocumentRepository:
        return SqlAlchemyDocumentRepository(session=self.session)

    @cached_property
    def document_processing_result_repository(
        self,
    ) -> SqlAlchemyDocumentProcessingResultRepository:
        return SqlAlchemyDocumentProcessingResultRepository(session=self.session)

    @cached_property
    def membership_authorization_service(self) -> MembershipAuthorizationService:
        return MembershipAuthorizationService()

    @cached_property
    def build_authenticated_session_user_use_case(self) -> BuildAuthenticatedSessionUserUseCase:
        return BuildAuthenticatedSessionUserUseCase(
            authenticated_membership_use_case=self.get_authenticated_membership_use_case,
            organization_repository=self.organization_repository,
        )

    @cached_property
    def get_authenticated_membership_use_case(self) -> GetAuthenticatedMembershipUseCase:
        return GetAuthenticatedMembershipUseCase(
            organization_membership_repository=self.organization_membership_repository,
        )

    @cached_property
    def login_user_use_case(self) -> LoginUserUseCase:
        return LoginUserUseCase(
            user_repository=self.user_repository,
            auth_session_repository=self.auth_session_repository,
            password_hasher=self.password_hasher,
            token_service=self.token_service,
            access_token_ttl_seconds=self.settings.auth_access_token_ttl_seconds,
            refresh_token_ttl_seconds=self.settings.auth_refresh_token_ttl_seconds,
            authenticated_session_user_use_case=self.build_authenticated_session_user_use_case,
        )

    @cached_property
    def refresh_session_use_case(self) -> RefreshSessionUseCase:
        return RefreshSessionUseCase(
            user_repository=self.user_repository,
            auth_session_repository=self.auth_session_repository,
            token_service=self.token_service,
            access_token_ttl_seconds=self.settings.auth_access_token_ttl_seconds,
            refresh_token_ttl_seconds=self.settings.auth_refresh_token_ttl_seconds,
            authenticated_session_user_use_case=self.build_authenticated_session_user_use_case,
        )

    @cached_property
    def logout_session_use_case(self) -> LogoutSessionUseCase:
        return LogoutSessionUseCase(
            auth_session_repository=self.auth_session_repository,
            token_service=self.token_service,
        )

    @cached_property
    def get_authenticated_user_use_case(self) -> GetAuthenticatedUserUseCase:
        return GetAuthenticatedUserUseCase(
            user_repository=self.user_repository,
            token_service=self.token_service,
        )

    @cached_property
    def list_authenticated_memberships_use_case(self) -> ListAuthenticatedMembershipsUseCase:
        return ListAuthenticatedMembershipsUseCase(
            organization_membership_repository=self.organization_membership_repository,
            organization_repository=self.organization_repository,
        )

    @cached_property
    def create_user_use_case(self) -> CreateUserUseCase:
        return CreateUserUseCase(
            user_repository=self.user_repository,
            password_hasher=self.password_hasher,
        )

    @cached_property
    def create_organization_use_case(self) -> CreateOrganizationUseCase:
        return CreateOrganizationUseCase(
            organization_repository=self.organization_repository,
        )

    @cached_property
    def get_organization_by_id_use_case(self) -> GetOrganizationByIdUseCase:
        return GetOrganizationByIdUseCase(
            organization_repository=self.organization_repository,
        )

    @cached_property
    def create_organization_membership_use_case(self) -> CreateOrganizationMembershipUseCase:
        return CreateOrganizationMembershipUseCase(
            organization_membership_repository=self.organization_membership_repository,
            organization_repository=self.organization_repository,
            user_repository=self.user_repository,
        )

    @cached_property
    def get_organization_membership_use_case(self) -> GetOrganizationMembershipUseCase:
        return GetOrganizationMembershipUseCase(
            organization_membership_repository=self.organization_membership_repository,
        )

    @cached_property
    def list_organization_memberships_use_case(self) -> ListOrganizationMembershipsUseCase:
        return ListOrganizationMembershipsUseCase(
            organization_membership_repository=self.organization_membership_repository,
            user_repository=self.user_repository,
        )

    @cached_property
    def update_organization_membership_role_use_case(
        self,
    ) -> UpdateOrganizationMembershipRoleUseCase:
        return UpdateOrganizationMembershipRoleUseCase(
            organization_membership_repository=self.organization_membership_repository,
            authorization_service=self.membership_authorization_service,
        )

    @cached_property
    def update_organization_membership_status_use_case(
        self,
    ) -> UpdateOrganizationMembershipStatusUseCase:
        return UpdateOrganizationMembershipStatusUseCase(
            organization_membership_repository=self.organization_membership_repository,
            authorization_service=self.membership_authorization_service,
        )

    @cached_property
    def create_request_use_case(self) -> CreateRequestUseCase:
        return CreateRequestUseCase(
            request_repository=self.request_repository,
            request_activity_repository=self.request_activity_repository,
            request_status_history_repository=self.request_status_history_repository,
            organization_repository=self.organization_repository,
            organization_membership_repository=self.organization_membership_repository,
            customer_repository=self.customer_repository,
        )

    @cached_property
    def list_requests_use_case(self) -> ListRequestsUseCase:
        return ListRequestsUseCase(
            request_repository=self.request_repository,
            document_repository=self.document_repository,
            request_comment_repository=self.request_comment_repository,
            customer_repository=self.customer_repository,
        )

    @cached_property
    def get_request_by_id_use_case(self) -> GetRequestByIdUseCase:
        return GetRequestByIdUseCase(
            request_repository=self.request_repository,
            document_repository=self.document_repository,
            request_comment_repository=self.request_comment_repository,
            customer_repository=self.customer_repository,
        )

    @cached_property
    def update_request_use_case(self) -> UpdateRequestUseCase:
        return UpdateRequestUseCase(
            request_repository=self.request_repository,
            request_activity_repository=self.request_activity_repository,
            document_repository=self.document_repository,
            request_comment_repository=self.request_comment_repository,
            customer_repository=self.customer_repository,
        )

    @cached_property
    def list_request_activities_use_case(self) -> ListRequestActivitiesUseCase:
        return ListRequestActivitiesUseCase(
            request_repository=self.request_repository,
            request_activity_repository=self.request_activity_repository,
            organization_membership_repository=self.organization_membership_repository,
        )

    @cached_property
    def list_request_comments_use_case(self) -> ListRequestCommentsUseCase:
        return ListRequestCommentsUseCase(
            request_repository=self.request_repository,
            request_comment_repository=self.request_comment_repository,
        )

    @cached_property
    def create_request_comment_use_case(self) -> CreateRequestCommentUseCase:
        return CreateRequestCommentUseCase(
            request_repository=self.request_repository,
            request_comment_repository=self.request_comment_repository,
            request_activity_repository=self.request_activity_repository,
        )

    @cached_property
    def transition_request_status_use_case(self) -> TransitionRequestStatusUseCase:
        return TransitionRequestStatusUseCase(
            request_repository=self.request_repository,
            request_activity_repository=self.request_activity_repository,
            organization_membership_repository=self.organization_membership_repository,
            request_status_history_repository=self.request_status_history_repository,
            document_repository=self.document_repository,
            request_comment_repository=self.request_comment_repository,
            customer_repository=self.customer_repository,
        )

    @cached_property
    def assign_request_use_case(self) -> AssignRequestUseCase:
        return AssignRequestUseCase(
            request_repository=self.request_repository,
            request_activity_repository=self.request_activity_repository,
            organization_membership_repository=self.organization_membership_repository,
            document_repository=self.document_repository,
            request_comment_repository=self.request_comment_repository,
            customer_repository=self.customer_repository,
        )

    @cached_property
    def create_document_use_case(self) -> CreateDocumentUseCase:
        return CreateDocumentUseCase(
            document_repository=self.document_repository,
            request_repository=self.request_repository,
            organization_membership_repository=self.organization_membership_repository,
            request_activity_repository=self.request_activity_repository,
        )

    @cached_property
    def upload_document_use_case(self) -> UploadDocumentUseCase:
        return UploadDocumentUseCase(
            document_storage=self.document_storage,
            create_document_use_case=self.create_document_use_case,
        )

    @cached_property
    def get_document_by_id_use_case(self) -> GetDocumentByIdUseCase:
        return GetDocumentByIdUseCase(document_repository=self.document_repository)

    @cached_property
    def list_request_documents_use_case(self) -> ListRequestDocumentsUseCase:
        return ListRequestDocumentsUseCase(
            document_repository=self.document_repository,
            request_repository=self.request_repository,
        )

    @cached_property
    def enqueue_document_processing_use_case(self) -> EnqueueDocumentProcessingUseCase:
        return EnqueueDocumentProcessingUseCase(
            document_repository=self.document_repository,
            document_processing_dispatcher=self.document_processing_dispatcher,
        )

    @cached_property
    def update_document_verified_data_use_case(self) -> UpdateDocumentVerifiedDataUseCase:
        return UpdateDocumentVerifiedDataUseCase(
            document_repository=self.document_repository,
            request_activity_repository=self.request_activity_repository,
        )

    @cached_property
    def get_document_processing_result_by_document_id_use_case(
        self,
    ) -> GetDocumentProcessingResultByDocumentIdUseCase:
        return GetDocumentProcessingResultByDocumentIdUseCase(
            document_repository=self.document_repository,
            document_processing_result_repository=self.document_processing_result_repository,
        )

    @cached_property
    def pipeline_analytics_service(self) -> PipelineAnalyticsService:
        return PipelineAnalyticsService(
            pipeline_analytics_repository=SqlAlchemyPipelineAnalyticsRepository(
                session=self.session
            ),
            bottleneck_threshold_days=self.settings.analytics_pipeline_bottleneck_threshold_days,
        )

    @cached_property
    def list_demo_intake_scenarios_use_case(self) -> ListDemoIntakeScenariosUseCase:
        return ListDemoIntakeScenariosUseCase()

    @cached_property
    def run_demo_intake_scenario_use_case(self) -> RunDemoIntakeScenarioUseCase:
        return RunDemoIntakeScenarioUseCase(
            create_request_use_case=self.create_request_use_case,
            upload_document_use_case=self.upload_document_use_case,
            enqueue_document_processing_use_case=self.enqueue_document_processing_use_case,
            create_request_comment_use_case=self.create_request_comment_use_case,
        )


def build_document_processing_worker(
    *,
    session_factory,
    document_storage: DocumentStorage,
) -> DocumentProcessingWorker:
    return DocumentProcessingWorker(
        session_factory=session_factory,
        document_processor=StorageBackedDocumentProcessor(document_storage=document_storage),
    )


def build_process_document_use_case(
    *,
    session: AsyncSession,
    document_storage: DocumentStorage,
) -> ProcessDocumentUseCase:
    return ProcessDocumentUseCase(
        document_repository=SqlAlchemyDocumentRepository(session=session),
        document_processing_result_repository=SqlAlchemyDocumentProcessingResultRepository(
            session=session
        ),
        document_processor=StorageBackedDocumentProcessor(document_storage=document_storage),
    )


def build_health_service(settings: Settings) -> HealthService:
    return HealthService(settings=settings)
