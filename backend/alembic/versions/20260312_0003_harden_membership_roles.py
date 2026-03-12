"""harden organization membership roles"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260312_0003"
down_revision: str | None = "20260312_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

ROLE_ENUM_NAME = "organization_membership_role"


def upgrade() -> None:
    op.execute("UPDATE organization_memberships SET role = UPPER(BTRIM(role))")

    role_enum = sa.Enum(
        "OWNER",
        "ADMIN",
        "MEMBER",
        name=ROLE_ENUM_NAME,
    )
    role_enum.create(op.get_bind(), checkfirst=True)

    op.execute(
        "ALTER TABLE organization_memberships "
        f"ALTER COLUMN role TYPE {ROLE_ENUM_NAME} "
        f"USING role::{ROLE_ENUM_NAME}"
    )


def downgrade() -> None:
    op.alter_column(
        "organization_memberships",
        "role",
        type_=sa.String(length=100),
        postgresql_using="role::text",
        existing_type=sa.Enum("OWNER", "ADMIN", "MEMBER", name=ROLE_ENUM_NAME),
    )
    sa.Enum("OWNER", "ADMIN", "MEMBER", name=ROLE_ENUM_NAME).drop(op.get_bind(), checkfirst=True)
