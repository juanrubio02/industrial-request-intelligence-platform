from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuthSession:
    id: UUID
    user_id: UUID
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    revoked_at: datetime | None = None
    replaced_by_session_id: UUID | None = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.now(UTC)
