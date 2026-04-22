"""harden request status history tenant fk"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260316_0015"
down_revision: str | None = "20260314_0014"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_requests_id_organization_id",
        "requests",
        ["id", "organization_id"],
    )
    op.drop_constraint(
        "request_status_history_request_id_fkey",
        "request_status_history",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_request_status_history_request_id_organization_id_requests",
        "request_status_history",
        "requests",
        ["request_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_request_status_history_request_id_organization_id_requests",
        "request_status_history",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "request_status_history_request_id_fkey",
        "request_status_history",
        "requests",
        ["request_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "uq_requests_id_organization_id",
        "requests",
        type_="unique",
    )
