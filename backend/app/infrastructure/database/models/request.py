from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.requests.sources import RequestSource
from app.domain.requests.statuses import RequestStatus
from app.infrastructure.database.base import Base


class RequestModel(Base):
    __tablename__ = "requests"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_requests_id_organization_id",
        ),
        ForeignKeyConstraint(
            ["customer_id", "organization_id"],
            ["customers.id", "customers.organization_id"],
            ondelete="RESTRICT",
            name="fk_requests_customer_id_organization_id_customers",
        ),
        Index("ix_requests_organization_id", "organization_id"),
        Index("ix_requests_status", "status"),
        Index("ix_requests_customer_id", "customer_id"),
        Index("ix_requests_assigned_membership_id", "assigned_membership_id"),
        Index(
            "ix_requests_org_status_created_at",
            "organization_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_requests_org_customer_created_at",
            "organization_id",
            "customer_id",
            "created_at",
        ),
        Index(
            "ix_requests_org_assignee_created_at",
            "organization_id",
            "assigned_membership_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            name="request_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    source: Mapped[RequestSource] = mapped_column(
        Enum(
            RequestSource,
            name="request_source",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    created_by_membership_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization_memberships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[UUID | None] = mapped_column(nullable=True)
    assigned_membership_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organization_memberships.id", ondelete="RESTRICT"),
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
