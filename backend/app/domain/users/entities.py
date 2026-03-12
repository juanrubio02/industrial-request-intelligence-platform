from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    full_name: str
    password_hash: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
