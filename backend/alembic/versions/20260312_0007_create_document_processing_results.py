"""create document processing results table"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260312_0007"
down_revision: str | None = "20260312_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    document_processing_result_status = postgresql.ENUM(
        "PROCESSED",
        "FAILED",
        name="document_processing_result_status",
        create_type=False,
    )
    document_processing_result_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "document_processing_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("status", document_processing_result_status, nullable=False),
        sa.Column("extracted_text", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("detected_document_type", sa.String(length=255), nullable=True),
        sa.Column("structured_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            name="uq_document_processing_results_document_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("document_processing_results")
    postgresql.ENUM(
        name="document_processing_result_status"
    ).drop(op.get_bind(), checkfirst=True)
