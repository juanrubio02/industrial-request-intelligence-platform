from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus


class OrganizationMembershipReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrganizationMembershipRole
    status: OrganizationMembershipStatus
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        return self.status == OrganizationMembershipStatus.ACTIVE


class OrganizationMembershipOptionReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    user_full_name: str
    user_email: str
    role: OrganizationMembershipRole
    status: OrganizationMembershipStatus
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        return self.status == OrganizationMembershipStatus.ACTIVE
