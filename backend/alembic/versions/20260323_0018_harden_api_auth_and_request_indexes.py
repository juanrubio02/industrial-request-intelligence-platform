"""harden auth roles and add request indexes"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260323_0018"
down_revision: str | None = "20260316_0017"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

ROLE_ENUM_NAME = "organization_membership_role"


def upgrade() -> None:
    op.execute(
        """
        UPDATE organization_memberships
        SET role = CASE
            WHEN role = 'MANAGER' THEN 'ADMIN'
            WHEN role = 'VIEWER' THEN 'MEMBER'
            ELSE role
        END
        """
    )

    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = '{ROLE_ENUM_NAME}'
            ) THEN
                ALTER TYPE {ROLE_ENUM_NAME} RENAME TO {ROLE_ENUM_NAME}_old;
            END IF;
        END
        $$;
        """
    )

    role_enum = sa.Enum("OWNER", "ADMIN", "MEMBER", name=ROLE_ENUM_NAME)
    role_enum.create(op.get_bind(), checkfirst=True)

    op.execute(
        f"""
        ALTER TABLE organization_memberships
        ALTER COLUMN role TYPE {ROLE_ENUM_NAME}
        USING role::text::{ROLE_ENUM_NAME}
        """
    )

    op.execute(f"DROP TYPE IF EXISTS {ROLE_ENUM_NAME}_old")

    op.create_index(
        "ix_requests_organization_id",
        "requests",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_requests_status",
        "requests",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_requests_customer_id",
        "requests",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_requests_assigned_membership_id",
        "requests",
        ["assigned_membership_id"],
        unique=False,
    )
    op.create_index(
        "ix_requests_org_status_created_at",
        "requests",
        ["organization_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_requests_org_customer_created_at",
        "requests",
        ["organization_id", "customer_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_requests_org_assignee_created_at",
        "requests",
        ["organization_id", "assigned_membership_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_requests_org_assignee_created_at", table_name="requests")
    op.drop_index("ix_requests_org_customer_created_at", table_name="requests")
    op.drop_index("ix_requests_org_status_created_at", table_name="requests")
    op.drop_index("ix_requests_assigned_membership_id", table_name="requests")
    op.drop_index("ix_requests_customer_id", table_name="requests")
    op.drop_index("ix_requests_status", table_name="requests")
    op.drop_index("ix_requests_organization_id", table_name="requests")

    role_enum = sa.Enum("OWNER", "ADMIN", "MEMBER", "MANAGER", "VIEWER", name=ROLE_ENUM_NAME)
    role_enum.create(op.get_bind(), checkfirst=True)
    op.execute(
        f"""
        ALTER TABLE organization_memberships
        ALTER COLUMN role TYPE {ROLE_ENUM_NAME}
        USING role::text::{ROLE_ENUM_NAME}
        """
    )
