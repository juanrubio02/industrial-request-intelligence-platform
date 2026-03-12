from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrganizationReadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

