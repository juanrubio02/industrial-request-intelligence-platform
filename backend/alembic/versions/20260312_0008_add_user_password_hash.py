"""add password hash to users"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260312_0008"
down_revision: str | None = "20260312_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
