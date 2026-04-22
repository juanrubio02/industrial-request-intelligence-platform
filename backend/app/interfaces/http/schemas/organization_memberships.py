from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus


class CreateOrganizationMembershipRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: UUID
    role: OrganizationMembershipRole


class UpdateOrganizationMembershipRoleRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    role: OrganizationMembershipRole


class UpdateOrganizationMembershipStatusRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    status: OrganizationMembershipStatus
