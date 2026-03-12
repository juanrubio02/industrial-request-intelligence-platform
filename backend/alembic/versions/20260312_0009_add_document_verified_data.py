"""add document verified structured data"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260312_0009"
down_revision: str | None = "20260312_0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "verified_structured_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.execute(
        "ALTER TYPE request_activity_type "
        "ADD VALUE IF NOT EXISTS 'DOCUMENT_VERIFIED_DATA_UPDATED'"
    )


def downgrade() -> None:
    op.drop_column("documents", "verified_structured_data")
    op.execute(
        "DELETE FROM request_activities "
        "WHERE type = 'DOCUMENT_VERIFIED_DATA_UPDATED'"
    )
    op.execute("ALTER TYPE request_activity_type RENAME TO request_activity_type_old")
    op.execute(
        "CREATE TYPE request_activity_type AS ENUM ("
        "'REQUEST_CREATED', "
        "'STATUS_CHANGED', "
        "'COMMENT_ADDED', "
        "'DOCUMENT_UPLOADED', "
        "'NOTE_ADDED'"
        ")"
    )
    op.execute(
        "ALTER TABLE request_activities "
        "ALTER COLUMN type TYPE request_activity_type "
        "USING type::text::request_activity_type"
    )
    op.execute("DROP TYPE request_activity_type_old")
