"""create request status history"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260313_0012"
down_revision: str | None = "20260312_0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
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
    request_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "request_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("previous_status", request_status, nullable=True),
        sa.Column("new_status", request_status, nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("changed_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["changed_by"],
            ["organization_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_request_status_history_org_changed_at",
        "request_status_history",
        ["organization_id", "changed_at"],
    )
    op.create_index(
        "ix_request_status_history_request_changed_at",
        "request_status_history",
        ["request_id", "changed_at"],
    )
    op.execute(
        """
        INSERT INTO request_status_history (
            id,
            request_id,
            organization_id,
            previous_status,
            new_status,
            changed_at,
            changed_by
        )
        SELECT
            gen_random_uuid(),
            id,
            organization_id,
            NULL,
            status,
            created_at,
            created_by_membership_id
        FROM requests
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_request_status_history_request_changed_at",
        table_name="request_status_history",
    )
    op.drop_index(
        "ix_request_status_history_org_changed_at",
        table_name="request_status_history",
    )
    op.drop_table("request_status_history")
