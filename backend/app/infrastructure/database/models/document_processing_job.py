from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.document_processing_jobs.statuses import DocumentProcessingJobStatus
from app.infrastructure.database.base import Base


class DocumentProcessingJobModel(Base):
    __tablename__ = "document_processing_jobs"
    __table_args__ = (
        Index("ix_document_processing_jobs_status_created_at", "status", "created_at"),
        Index("ix_document_processing_jobs_document_id", "document_id"),
        Index("ix_document_processing_jobs_organization_id", "organization_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[DocumentProcessingJobStatus] = mapped_column(
        Enum(
            DocumentProcessingJobStatus,
            name="document_processing_job_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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
