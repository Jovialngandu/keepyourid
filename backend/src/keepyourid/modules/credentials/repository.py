
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.modules.credentials.models import VerifiableCredential


class CredentialRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, credential: VerifiableCredential) -> VerifiableCredential:
        self.session.add(credential)
        self.session.commit()
        self.session.refresh(credential)
        return credential

    def get_by_id(self, credential_id: UUID) -> VerifiableCredential | None:
        return self.session.get(VerifiableCredential, credential_id)

    def get_by_credential_id(
        self,
        credential_id: str,
    ) -> VerifiableCredential | None:
        statement = select(VerifiableCredential).where(
            VerifiableCredential.credential_id == credential_id
        )
        return self.session.scalar(statement)

    def list_by_organization(
        self,
        organization_id: UUID,
    ) -> list[VerifiableCredential]:
        statement = (
            select(VerifiableCredential)
            .where(VerifiableCredential.organization_id == organization_id)
            .order_by(VerifiableCredential.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def list_by_holder_user(
        self,
        user_id: UUID,
    ) -> list[VerifiableCredential]:
        from keepyourid.modules.holders.models import HolderDID

        statement = (
            select(VerifiableCredential)
            .join(HolderDID, HolderDID.id == VerifiableCredential.holder_did_id)
            .where(HolderDID.user_id == user_id)
            .order_by(VerifiableCredential.created_at.desc())
        )
        return list(self.session.scalars(statement).all())
