import pytest
from datetime import UTC, datetime
from uuid import uuid4

from app.application.auth.authorization import (
    MembershipAuthorizationService,
    MembershipPermission,
)
from app.application.auth.exceptions import MembershipPermissionDeniedError
from app.application.auth.schemas import AuthenticatedMembershipReadModel
from app.domain.organization_memberships.roles import OrganizationMembershipRole


def _membership(role: OrganizationMembershipRole) -> AuthenticatedMembershipReadModel:
    now = datetime.now(UTC)
    return AuthenticatedMembershipReadModel(
        id=uuid4(),
        organization_id=uuid4(),
        user_id=uuid4(),
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def test_membership_authorization_service_allows_member_to_create_request() -> None:
    service = MembershipAuthorizationService()

    service.authorize(
        membership=_membership(OrganizationMembershipRole.MEMBER),
        permission=MembershipPermission.CREATE_REQUEST,
    )


def test_membership_authorization_service_rejects_member_for_status_transition() -> None:
    service = MembershipAuthorizationService()

    with pytest.raises(MembershipPermissionDeniedError):
        service.authorize(
            membership=_membership(OrganizationMembershipRole.MEMBER),
            permission=MembershipPermission.TRANSITION_REQUEST_STATUS,
        )
