"""create customers and link requests"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260314_0014"
down_revision: str | None = "20260313_0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "organization_id",
            name="uq_customers_id_organization_id",
        ),
    )

    op.add_column(
        "requests",
        sa.Column("customer_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_requests_customer_id_organization_id_customers",
        "requests",
        "customers",
        ["customer_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_requests_customer_id_organization_id_customers",
        "requests",
        type_="foreignkey",
    )
    op.drop_column("requests", "customer_id")
    op.drop_table("customers")
