from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus


@dataclass(frozen=True, slots=True)
class OrganizationMembership:
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrganizationMembershipRole
    status: OrganizationMembershipStatus
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    @property
    def is_active(self) -> bool:
        return self.status == OrganizationMembershipStatus.ACTIVE
