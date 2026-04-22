"""add request updated activity"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260316_0017"
down_revision: str | None = "20260316_0016"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE request_activity_type "
        "ADD VALUE IF NOT EXISTS 'REQUEST_UPDATED'"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM request_activities "
        "WHERE type = 'REQUEST_UPDATED'"
    )
    op.execute("ALTER TYPE request_activity_type RENAME TO request_activity_type_old")
    op.execute(
        "CREATE TYPE request_activity_type AS ENUM ("
        "'REQUEST_CREATED', "
        "'REQUEST_ASSIGNED', "
        "'REQUEST_COMMENT_ADDED', "
        "'STATUS_CHANGED', "
        "'COMMENT_ADDED', "
        "'DOCUMENT_UPLOADED', "
        "'DOCUMENT_VERIFIED_DATA_UPDATED', "
        "'NOTE_ADDED'"
        ")"
    )
    op.execute(
        "ALTER TABLE request_activities "
        "ALTER COLUMN type TYPE request_activity_type "
        "USING type::text::request_activity_type"
    )
    op.execute("DROP TYPE request_activity_type_old")
