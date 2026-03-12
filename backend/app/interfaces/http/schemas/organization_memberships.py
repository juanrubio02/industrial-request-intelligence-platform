from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.organization_memberships.roles import OrganizationMembershipRole


class CreateOrganizationMembershipRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: UUID
    role: OrganizationMembershipRole
