"""add request status history actor user"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260316_0016"
down_revision: str | None = "20260316_0015"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "request_status_history",
        sa.Column("changed_by_user_id", sa.Uuid(), nullable=True),
    )
    op.execute(
        """
        UPDATE request_status_history AS history
        SET changed_by_user_id = membership.user_id
        FROM organization_memberships AS membership
        WHERE membership.id = history.changed_by
        """
    )
    op.alter_column(
        "request_status_history",
        "changed_by_user_id",
        nullable=False,
    )
    op.create_foreign_key(
        "fk_request_status_history_changed_by_user_id_users",
        "request_status_history",
        "users",
        ["changed_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_request_status_history_changed_by_user_id_users",
        "request_status_history",
        type_="foreignkey",
    )
    op.drop_column("request_status_history", "changed_by_user_id")
