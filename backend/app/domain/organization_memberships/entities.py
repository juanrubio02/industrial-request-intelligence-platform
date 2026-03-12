from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.organization_memberships.roles import OrganizationMembershipRole


@dataclass(frozen=True, slots=True)
class OrganizationMembership:
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrganizationMembershipRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
