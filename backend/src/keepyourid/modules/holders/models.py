from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from keepyourid.core.database import Base
from keepyourid.modules.dids.enums import DIDStatus


class HolderDID(Base):
    __tablename__ = "holder_dids"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    identifier: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
    )

    method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    document: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
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

    status: Mapped[DIDStatus] = mapped_column(
        Enum(
            DIDStatus,
            name="holder_did_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=DIDStatus.REGISTERED,
        nullable=False,
    )


class HolderDIDChallenge(Base):
    __tablename__ = "holder_did_challenges"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    holder_did_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("holder_dids.id", ondelete="CASCADE"),
        nullable=False,
    )

    @property
    def did_id(self) -> UUID:
        return self.holder_did_id

    @did_id.setter
    def did_id(self, value: UUID) -> None:
        self.holder_did_id = value

    challenge: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )

    purpose: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
