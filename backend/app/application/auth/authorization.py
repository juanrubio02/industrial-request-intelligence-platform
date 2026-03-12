from enum import StrEnum

from app.application.auth.exceptions import MembershipPermissionDeniedError
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.domain.organization_memberships.roles import OrganizationMembershipRole


class MembershipPermission(StrEnum):
    CREATE_REQUEST = "CREATE_REQUEST"
    CREATE_DOCUMENT = "CREATE_DOCUMENT"
    UPLOAD_DOCUMENT = "UPLOAD_DOCUMENT"
    TRANSITION_REQUEST_STATUS = "TRANSITION_REQUEST_STATUS"
    ENQUEUE_DOCUMENT_PROCESSING = "ENQUEUE_DOCUMENT_PROCESSING"


_ALLOWED_ROLES_BY_PERMISSION: dict[
    MembershipPermission,
    frozenset[OrganizationMembershipRole],
] = {
    MembershipPermission.CREATE_REQUEST: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
            OrganizationMembershipRole.MEMBER,
        }
    ),
    MembershipPermission.CREATE_DOCUMENT: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
            OrganizationMembershipRole.MEMBER,
        }
    ),
    MembershipPermission.UPLOAD_DOCUMENT: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
            OrganizationMembershipRole.MEMBER,
        }
    ),
    MembershipPermission.TRANSITION_REQUEST_STATUS: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
        }
    ),
    MembershipPermission.ENQUEUE_DOCUMENT_PROCESSING: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
        }
    ),
}


class MembershipAuthorizationService:
    def authorize(
        self,
        *,
        membership: AuthenticatedMembershipReadModel,
        permission: MembershipPermission,
    ) -> None:
        allowed_roles = _ALLOWED_ROLES_BY_PERMISSION[permission]
        if membership.role not in allowed_roles:
            raise MembershipPermissionDeniedError(
                f"Membership role '{membership.role.value}' is not allowed to perform '{permission.value}'."
            )
