
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum

from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.core.database import Base


class DID(Base):
	__tablename__ = "dids"

	id: Mapped[UUID] = mapped_column(
		PG_UUID(as_uuid=True),
		primary_key=True,
		default=uuid4,
	)

	organization_id: Mapped[UUID] = mapped_column(
		PG_UUID(as_uuid=True),
		ForeignKey("organizations.id", ondelete="CASCADE"),
		unique=True,
		nullable=False,
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
		Enum(DIDStatus, name="did_status"),
		default=DIDStatus.REGISTERED,
		nullable=False,
	)

