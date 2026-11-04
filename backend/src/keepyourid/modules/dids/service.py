
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keepyourid.modules.dids.challenge_service import (
    DIDChallengeService,
    DIDNotFoundError,
)
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.dids.repository import DIDRepository
from keepyourid.modules.dids.schemas import DIDCreate, DIDProofSubmission
from keepyourid.modules.dids.verification.service import (
    DIDVerificationService,
)
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization


class OrganizationNotFoundError(Exception):
    pass


class OrganizationInactiveError(Exception):
    pass


class DIDAlreadyExistsError(Exception):
    pass

class DIDAlreadyVerifiedError(Exception):
    pass


class DIDService:
    def __init__(self, session: Session, issuer_registry_service=None):
        self.session = session
        self.repository = DIDRepository(session)
        self.issuer_registry_service = issuer_registry_service

    def get(self, did_id: UUID) -> DID | None:
        return self.repository.get_by_id(did_id)

    def list_by_organization(self, organization_id: UUID) -> list[DID]:
        return self.repository.list_by_organization(organization_id)

    def register(
        self,
        organization_id: UUID,
        data: DIDCreate,
    ) -> DID:
        organization = self.session.get(Organization, organization_id)

        if organization is None:
            raise OrganizationNotFoundError("Organization not found.")

        if organization.status != OrganizationStatus.ACTIVE:
            raise OrganizationInactiveError(
                "Organization must be active to register a DID."
            )

        if self.repository.get_by_organization(organization_id):
            raise DIDAlreadyExistsError(
                "This organization already has a DID."
            )

        identifier = data.identifier.strip()

        if self.repository.get_by_identifier(identifier):
            raise DIDAlreadyExistsError(
                "This DID identifier is already registered."
            )

        did = DID(
            organization_id=organization_id,
            identifier=identifier,
            method=data.method.strip().lower(),
            document=data.document,
        )

        try:
            created = self.repository.create(did)
            organization.did = created.identifier
            self.session.commit()
            self.session.refresh(organization)
            return created
        except IntegrityError as exc:
            self.session.rollback()
            raise DIDAlreadyExistsError(
                "The DID or organization association already exists."
            ) from exc
            
    
    
    def verify_control(
        self,
        did_id: UUID,
        proof: DIDProofSubmission,
        verifier: DIDVerificationService,
    ) -> dict:
        did = self.session.get(DID, did_id)

        if did is None:
            raise DIDNotFoundError("DID not found.")

        if did.status == DIDStatus.VERIFIED:
            raise DIDAlreadyVerifiedError(
                "This DID has already been verified."
            )

        challenge_service = DIDChallengeService(self.session)

        try:
            challenge = challenge_service.validate_challenge(
                proof.challenge_id,
                did_id=did.id,
                purpose="did_authentication",
            )

            result = verifier.verify_authentication(
                did=did.identifier,
                challenge=challenge.challenge,
                purpose=challenge.purpose,
                domain=challenge.domain,
                issued_at=challenge.issued_at,
                expires_at=challenge.expires_at,
                verification_method=proof.verification_method,
                signature=proof.signature,
                did_document=did.document,
                
            )

            challenge_service.consume_challenge(
                challenge_id=challenge.id,
                did_id=did.id,
                purpose=challenge.purpose,
                domain=challenge.domain,
            )

            did.status = DIDStatus.VERIFIED

            self.session.commit()
            self.session.refresh(did)

            blockchain_result = None
            if self.issuer_registry_service is not None:
                organization = self.session.get(Organization, did.organization_id)
                metadata = {
                    "organization_id": str(did.organization_id),
                    "organization_name": organization.legal_name if organization else None,
                    "did_id": str(did.id),
                }
                try:
                    blockchain_result = self.issuer_registry_service.register_issuer(
                        organization_id=did.organization_id,
                        did_id=did.id,
                        did=did.identifier,
                        metadata=metadata,
                    )
                except Exception as exc:  # pragma: no cover - defensive boundary
                    blockchain_result = {
                        "status": "PENDING",
                        "error": str(exc),
                    }

            response = {
                "did_id": did.id,
                "identifier": did.identifier,
                "status": did.status.value,
                "verification_method": result["verification_method"],
                "signer_address": result["signer_address"],
                "verified_at": datetime.now(timezone.utc),
            }
            if blockchain_result is not None:
                response["blockchain_registration"] = blockchain_result

            return response

        except Exception:
            self.session.rollback()
            raise

