from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from keepyourid.core.database import Base
from keepyourid.modules.organizations.enums import OrganizationStatus


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    did: Mapped[str | None] = mapped_column(
        String(500),
        unique=True,
        nullable=True,
    )



    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    
    status: Mapped[OrganizationStatus] = mapped_column(
    Enum(
        OrganizationStatus,
        name="organization_status",
        values_callable=lambda enum: [item.value for item in enum],
    ),
    default=OrganizationStatus.ACTIVE,
    nullable=False,
)