
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.modules.dids.models import DID


class DIDRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, did_id: UUID) -> DID | None:
        return self.session.get(DID, did_id)

    def get_by_organization(self, organization_id: UUID) -> DID | None:
        return self.session.scalar(
            select(DID).where(
                DID.organization_id == organization_id
            )
        )

    def get_by_identifier(self, identifier: str) -> DID | None:
        return self.session.scalar(
            select(DID).where(DID.identifier == identifier)
        )

    def create(self, did: DID) -> DID:
        self.session.add(did)
        self.session.commit()
        self.session.refresh(did)
        return did
