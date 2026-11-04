from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from keepyourid.modules.credentials.models import VerifiableCredential
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.verification.service import DIDVerificationService
from keepyourid.modules.holders.challenge_service import (
    HolderDIDChallengeService,
    HolderDIDNotFoundError,
)
from keepyourid.modules.holders.models import HolderDID
from keepyourid.modules.users.models import User


class HolderDIDAlreadyExistsError(Exception):
    pass


class HolderDIDNotFoundError(Exception):
    pass


class HolderUserNotFoundError(Exception):
    pass


class HolderDIDService:
    def __init__(self, session: Session):
        self.session = session

    def register_user_did(
        self,
        user_id: UUID,
        identifier: str,
        method: str,
        document: dict,
    ) -> HolderDID:
        user = self.session.get(User, user_id)
        if user is None:
            raise HolderUserNotFoundError("User not found.")

        normalized_identifier = (identifier or "").strip()
        if not normalized_identifier:
            raise ValueError("DID identifier is required.")

        existing = self.session.scalar(
            select(HolderDID).where(HolderDID.identifier == normalized_identifier)
        )
        if existing is not None:
            raise HolderDIDAlreadyExistsError("This DID identifier is already registered.")

        did = HolderDID(
            user_id=user_id,
            identifier=normalized_identifier,
            method=(method or "ethr").strip().lower(),
            document=document or {},
        )
        self.session.add(did)
        self.session.commit()
        self.session.refresh(did)
        return did

    def get_user_did(self, user_id: UUID, did_id: UUID) -> HolderDID | None:
        did = self.session.get(HolderDID, did_id)
        if did is None or did.user_id != user_id:
            return None
        return did

    def list_user_dids(self, user_id: UUID) -> list[HolderDID]:
        statement = select(HolderDID).where(HolderDID.user_id == user_id).order_by(
            HolderDID.created_at.desc()
        )
        return list(self.session.scalars(statement).all())

    def list_user_credentials(self, user_id: UUID) -> list[VerifiableCredential]:
        statement = (
            select(VerifiableCredential)
            .join(HolderDID, HolderDID.id == VerifiableCredential.holder_did_id)
            .where(HolderDID.user_id == user_id)
            .order_by(VerifiableCredential.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def verify_holder_did(
        self,
        did_id: UUID,
        challenge_id: UUID,
        signature: str,
        verification_method: str,
        purpose: str,
        domain: str,
        did_document: dict | None = None,
    ) -> dict:
        did = self.session.get(HolderDID, did_id)
        if did is None:
            raise HolderDIDNotFoundError("Holder DID not found.")

        challenge_service = HolderDIDChallengeService(self.session)
        challenge = challenge_service.validate_challenge(
            challenge_id,
            holder_did_id=did.id,
            purpose=purpose,
            domain=domain,
        )

        result = DIDVerificationService().verify_authentication(
            did=did.identifier,
            challenge=challenge.challenge,
            purpose=challenge.purpose,
            domain=challenge.domain,
            issued_at=challenge.issued_at,
            expires_at=challenge.expires_at,
            verification_method=verification_method,
            signature=signature,
            did_document=did_document or did.document,
        )

        challenge_service.consume_challenge(
            challenge_id=challenge.id,
            holder_did_id=did.id,
            purpose=challenge.purpose,
            domain=challenge.domain,
        )

        did.status = DIDStatus.VERIFIED
        self.session.commit()
        self.session.refresh(did)

        return {
            "did_id": did.id,
            "identifier": did.identifier,
            "status": did.status.value,
            "verification_method": result["verification_method"],
            "signer_address": result["signer_address"],
            "holder_user_id": str(did.user_id),
            "verified_at": datetime.now(timezone.utc),
        }
