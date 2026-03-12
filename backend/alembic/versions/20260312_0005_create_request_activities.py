"""create request activities table"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260312_0005"
down_revision: str | None = "20260312_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    request_activity_type = postgresql.ENUM(
        "REQUEST_CREATED",
        "STATUS_CHANGED",
        "COMMENT_ADDED",
        "DOCUMENT_UPLOADED",
        "NOTE_ADDED",
        name="request_activity_type",
        create_type=False,
    )
    request_activity_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "request_activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("type", request_activity_type, nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["request_id"], ["requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["membership_id"], ["organization_memberships.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_request_activities_request_created_at",
        "request_activities",
        ["request_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_request_activities_request_created_at", table_name="request_activities")
    op.drop_table("request_activities")
    postgresql.ENUM(name="request_activity_type").drop(op.get_bind(), checkfirst=True)
