"""create requests table"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260312_0004"
down_revision: str | None = "20260312_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    request_status = postgresql.ENUM(
        "NEW",
        "UNDER_REVIEW",
        "QUOTE_PREPARING",
        "QUOTE_SENT",
        "NEGOTIATION",
        "WON",
        "LOST",
        name="request_status",
        create_type=False,
    )
    request_source = postgresql.ENUM(
        "EMAIL",
        "WEB_FORM",
        "API",
        "MANUAL",
        name="request_source",
        create_type=False,
    )
    request_status.create(op.get_bind(), checkfirst=True)
    request_source.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", request_status, nullable=False),
        sa.Column("source", request_source, nullable=False),
        sa.Column("created_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["created_by_membership_id"],
            ["organization_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("requests")
    postgresql.ENUM(name="request_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="request_source").drop(op.get_bind(), checkfirst=True)
