from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from keepyourid.core.database import Base


class CredentialStatusList(Base):
    __tablename__ = "credential_status_lists"

    __table_args__ = (
        UniqueConstraint(
            "issuer_did_id",
            name="uq_credential_status_lists_issuer_did",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    issuer_did_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dids.id", ondelete="CASCADE"),
        nullable=False,
    )

    # W3C Bitstring Status List: minimum 16 KB.
    bitstring: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        default=lambda: bytes(16 * 1024),
    )

    # Next available index for this issuer.
    next_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # Signed status-list credential published to verifiers.
    signed_credential: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    proof: Mapped[dict | None] = mapped_column(
        JSONB,
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