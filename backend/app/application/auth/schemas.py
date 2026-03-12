from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.domain.organization_memberships.roles import OrganizationMembershipRole


class AccessTokenReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    token_type: str = "bearer"


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
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AuthenticatedMembershipOptionReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    organization_name: str
    role: OrganizationMembershipRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
