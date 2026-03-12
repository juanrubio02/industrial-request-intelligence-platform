from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.organization_memberships.roles import OrganizationMembershipRole


class CreateOrganizationMembershipCommand(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    organization_id: UUID
    user_id: UUID
    role: OrganizationMembershipRole
