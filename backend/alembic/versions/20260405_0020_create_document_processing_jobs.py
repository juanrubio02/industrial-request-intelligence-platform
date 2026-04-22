"""create durable document processing jobs"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260405_0020"
down_revision: str | None = "20260323_0019"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    document_processing_job_status = sa.Enum(
        "PENDING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        name="document_processing_job_status",
    )

    op.create_table(
        "document_processing_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("status", document_processing_job_status, nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_processing_jobs_status_created_at",
        "document_processing_jobs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_document_processing_jobs_document_id",
        "document_processing_jobs",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_document_processing_jobs_organization_id",
        "document_processing_jobs",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_processing_jobs_organization_id",
        table_name="document_processing_jobs",
    )
    op.drop_index(
        "ix_document_processing_jobs_document_id",
        table_name="document_processing_jobs",
    )
    op.drop_index(
        "ix_document_processing_jobs_status_created_at",
        table_name="document_processing_jobs",
    )
    op.drop_table("document_processing_jobs")
