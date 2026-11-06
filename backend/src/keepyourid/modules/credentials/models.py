
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, func, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from keepyourid.core.database import Base
from keepyourid.modules.credentials.enums import CredentialStatus
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
    Text,
    UniqueConstraint,
)

class VerifiableCredential(Base):
    __tablename__ = "verifiable_credentials"
    __table_args__ = (
    UniqueConstraint(
        "issuer_did_id",
        "status_list_index",
        name="uq_credential_issuer_status_index",
    ),
)

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

    holder_did_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("holder_dids.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
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
    status_list_index: Mapped[int | None] = mapped_column(
    Integer,
    nullable=True,
	)
