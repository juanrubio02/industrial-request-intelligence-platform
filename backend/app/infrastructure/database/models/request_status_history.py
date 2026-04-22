from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, ForeignKeyConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.requests.statuses import RequestStatus
from app.infrastructure.database.base import Base


class RequestStatusHistoryModel(Base):
    __tablename__ = "request_status_history"
    __table_args__ = (
        ForeignKeyConstraint(
            ["request_id", "organization_id"],
            ["requests.id", "requests.organization_id"],
            ondelete="RESTRICT",
            name="fk_request_status_history_request_id_organization_id_requests",
        ),
        Index(
            "ix_request_status_history_org_changed_at",
            "organization_id",
            "changed_at",
        ),
        Index(
            "ix_request_status_history_request_changed_at",
            "request_id",
            "changed_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    request_id: Mapped[UUID] = mapped_column(nullable=False)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_status: Mapped[RequestStatus | None] = mapped_column(
        Enum(
            RequestStatus,
            name="request_status",
            values_callable=lambda enum: [item.value for item in enum],
            create_type=False,
        ),
        nullable=True,
    )
    new_status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            name="request_status",
            values_callable=lambda enum: [item.value for item in enum],
            create_type=False,
        ),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    changed_by: Mapped[UUID] = mapped_column(
        ForeignKey("organization_memberships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    changed_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
