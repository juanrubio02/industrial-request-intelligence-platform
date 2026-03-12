from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.document_processing_results.statuses import (
    DocumentProcessingResultStatus,
)
from app.infrastructure.database.base import Base


class DocumentProcessingResultModel(Base):
    __tablename__ = "document_processing_results"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_document_processing_results_document_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[DocumentProcessingResultStatus] = mapped_column(
        Enum(
            DocumentProcessingResultStatus,
            name="document_processing_result_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    extracted_text: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    detected_document_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    structured_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
