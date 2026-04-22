from enum import StrEnum

from app.application.auth.exceptions import MembershipPermissionDeniedError
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.domain.organization_memberships.roles import OrganizationMembershipRole


class MembershipPermission(StrEnum):
    VIEW_REQUESTS = "VIEW_REQUESTS"
    CREATE_REQUEST = "CREATE_REQUEST"
    COMMENT_ON_REQUEST = "COMMENT_ON_REQUEST"
    CREATE_DOCUMENT = "CREATE_DOCUMENT"
    UPLOAD_DOCUMENT = "UPLOAD_DOCUMENT"
    UPDATE_VERIFIED_DOCUMENT_DATA = "UPDATE_VERIFIED_DOCUMENT_DATA"
    TRANSITION_REQUEST_STATUS = "TRANSITION_REQUEST_STATUS"
    ASSIGN_REQUEST = "ASSIGN_REQUEST"
    ENQUEUE_DOCUMENT_PROCESSING = "ENQUEUE_DOCUMENT_PROCESSING"
    VIEW_ANALYTICS = "VIEW_ANALYTICS"
    VIEW_MEMBERS = "VIEW_MEMBERS"
    MANAGE_MEMBERS = "MANAGE_MEMBERS"
    CREATE_USER = "CREATE_USER"
    CREATE_ORGANIZATION = "CREATE_ORGANIZATION"


_ALLOWED_ROLES_BY_PERMISSION: dict[
    MembershipPermission,
    frozenset[OrganizationMembershipRole],
] = {
    MembershipPermission.VIEW_REQUESTS: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
            OrganizationMembershipRole.MEMBER,
        }
    ),
    MembershipPermission.CREATE_REQUEST: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
            OrganizationMembershipRole.MEMBER,
        }
    ),
    MembershipPermission.COMMENT_ON_REQUEST: frozenset(
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
    MembershipPermission.UPDATE_VERIFIED_DOCUMENT_DATA: frozenset(
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
            OrganizationMembershipRole.MEMBER,
        }
    ),
    MembershipPermission.ASSIGN_REQUEST: frozenset(
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
    MembershipPermission.VIEW_ANALYTICS: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
            OrganizationMembershipRole.MEMBER,
        }
    ),
    MembershipPermission.VIEW_MEMBERS: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
        }
    ),
    MembershipPermission.MANAGE_MEMBERS: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
        }
    ),
    MembershipPermission.CREATE_USER: frozenset(
        {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
        }
    ),
    MembershipPermission.CREATE_ORGANIZATION: frozenset(
        {
            OrganizationMembershipRole.OWNER,
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

    @staticmethod
    def can_manage_members(
        *,
        actor_membership: AuthenticatedMembershipReadModel,
    ) -> bool:
        return actor_membership.role in {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
        }

    @staticmethod
    def can_manage_target_membership(
        *,
        actor_membership: AuthenticatedMembershipReadModel,
        target_membership: AuthenticatedMembershipReadModel,
    ) -> bool:
        if actor_membership.role == OrganizationMembershipRole.OWNER:
            return True

        if actor_membership.role == OrganizationMembershipRole.ADMIN:
            return target_membership.role != OrganizationMembershipRole.OWNER

        return False

    @staticmethod
    def can_assign_role(
        *,
        actor_membership: AuthenticatedMembershipReadModel,
        role: OrganizationMembershipRole,
    ) -> bool:
        if actor_membership.role == OrganizationMembershipRole.OWNER:
            return True

        if actor_membership.role == OrganizationMembershipRole.ADMIN:
            return role != OrganizationMembershipRole.OWNER

        return False
