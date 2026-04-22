from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic import computed_field

from app.domain.organization_memberships.roles import OrganizationMembershipRole
from app.domain.organization_memberships.statuses import OrganizationMembershipStatus


class AccessTokenReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthenticatedUserReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AuthenticatedMembershipReadModel(BaseModel):
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


class AuthenticatedOrganizationReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    slug: str


class ActiveMembershipSummaryReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    role: OrganizationMembershipRole
    status: OrganizationMembershipStatus


class AuthenticatedMembershipOptionReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    organization_name: str
    organization_slug: str
    role: OrganizationMembershipRole
    status: OrganizationMembershipStatus
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        return self.status == OrganizationMembershipStatus.ACTIVE


class AuthenticatedSessionUserReadModel(AuthenticatedUserReadModel):
    active_organization: AuthenticatedOrganizationReadModel | None = None
    active_membership: ActiveMembershipSummaryReadModel | None = None


class AuthenticatedSessionReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    user: AuthenticatedSessionUserReadModel
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class LoginResponseReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    user: AuthenticatedSessionUserReadModel
    access_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
