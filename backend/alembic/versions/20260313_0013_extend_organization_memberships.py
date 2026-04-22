"""extend organization memberships with status and joined_at"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260313_0013"
down_revision: str | None = "20260313_0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

ROLE_ENUM_NAME = "organization_membership_role"
STATUS_ENUM_NAME = "organization_membership_status"


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname = '{ROLE_ENUM_NAME}' AND e.enumlabel = 'MANAGER'
            ) THEN
                ALTER TYPE {ROLE_ENUM_NAME} ADD VALUE 'MANAGER';
            END IF;
        END
        $$;
        """
    )
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname = '{ROLE_ENUM_NAME}' AND e.enumlabel = 'VIEWER'
            ) THEN
                ALTER TYPE {ROLE_ENUM_NAME} ADD VALUE 'VIEWER';
            END IF;
        END
        $$;
        """
    )

    status_enum = sa.Enum(
        "ACTIVE",
        "DISABLED",
        name=STATUS_ENUM_NAME,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "organization_memberships",
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.add_column(
        "organization_memberships",
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.execute(
        """
        UPDATE organization_memberships
        SET
            status = CASE
                WHEN is_active THEN 'ACTIVE'::organization_membership_status
                ELSE 'DISABLED'::organization_membership_status
            END,
            joined_at = created_at
        """
    )

    op.alter_column(
        "organization_memberships",
        "status",
        server_default=None,
    )
    op.alter_column(
        "organization_memberships",
        "joined_at",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("organization_memberships", "joined_at")
    op.drop_column("organization_memberships", "status")
    sa.Enum("ACTIVE", "DISABLED", name=STATUS_ENUM_NAME).drop(
        op.get_bind(),
        checkfirst=True,
    )
