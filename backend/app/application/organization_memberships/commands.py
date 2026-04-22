from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus


class CreateOrganizationMembershipCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    organization_id: UUID
    user_id: UUID
    role: OrganizationMembershipRole


class UpdateOrganizationMembershipRoleCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    organization_id: UUID
    actor_membership_id: UUID
    role: OrganizationMembershipRole


class UpdateOrganizationMembershipStatusCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    organization_id: UUID
    actor_membership_id: UUID
    status: OrganizationMembershipStatus
