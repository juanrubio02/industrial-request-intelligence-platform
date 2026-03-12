from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.organization_memberships.roles import OrganizationMembershipRole


class OrganizationMembershipReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrganizationMembershipRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
