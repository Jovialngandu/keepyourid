
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, func, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from keepyourid.core.database import Base
from keepyourid.modules.credentials.enums import CredentialStatus


class VerifiableCredential(Base):
    __tablename__ = "verifiable_credentials"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    credential_id: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
    )

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    issuer_did_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dids.id", ondelete="RESTRICT"),
        nullable=False,
    )

    credential_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    credential_subject: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    proof: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    status: Mapped[CredentialStatus] = mapped_column(
        Enum(
            CredentialStatus,
            name="credential_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=CredentialStatus.DRAFT,
        nullable=False,
    )

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
    
    signed_credential: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
)
