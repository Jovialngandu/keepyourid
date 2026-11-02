from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keepyourid.modules.credentials.enums import CredentialStatus
from keepyourid.modules.credentials.models import VerifiableCredential
from keepyourid.modules.credentials.repository import CredentialRepository
from keepyourid.modules.credentials.schemas import CredentialCreate
from keepyourid.modules.credentials.cryptography.jws import (
    JWSVerificationError,
    build_signing_input,
    complete_jws,
    verify_jws,
)
from keepyourid.modules.credentials.cryptography.issuer_keys import (
    IssuerKeyError,
    IssuerKeyResolver,
)
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization


class CredentialOrganizationNotFoundError(Exception):
    pass


class CredentialOrganizationInactiveError(Exception):
    pass


class CredentialDIDNotFoundError(Exception):
    pass


class CredentialDIDNotVerifiedError(Exception):
    pass


class CredentialInvalidDataError(Exception):
    pass


class CredentialAlreadyExistsError(Exception):
    pass


class CredentialService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = CredentialRepository(session)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _get_verified_issuer_did(
        self,
        organization_id: UUID,
    ) -> DID:
        organization = self.session.get(
            Organization,
            organization_id,
        )

        if organization is None:
            raise CredentialOrganizationNotFoundError(
                "Organization not found."
            )

        if organization.status != OrganizationStatus.ACTIVE:
            raise CredentialOrganizationInactiveError(
                "Organization must be active to issue credentials."
            )

        did = (
            self.session.query(DID)
            .filter(DID.organization_id == organization_id)
            .first()
        )

        if did is None:
            raise CredentialDIDNotFoundError(
                "Organization has no registered DID."
            )

        if did.status != DIDStatus.VERIFIED:
            raise CredentialDIDNotVerifiedError(
                "Organization DID must be verified first."
            )

        return did

    def _get_credential_or_raise(
        self,
        credential_id: UUID,
    ) -> VerifiableCredential:
        credential = self.repository.get_by_id(credential_id)

        if credential is None:
            raise CredentialInvalidDataError(
                "Credential not found."
            )

        return credential

    def _get_issuer_key(
        self,
        credential: VerifiableCredential,
    ) -> tuple[str, str]:
        try:
            return IssuerKeyResolver(self.session).resolve(
                credential
            )
        except IssuerKeyError as exc:
            raise CredentialInvalidDataError(
                f"Unable to resolve issuer signing key: {exc}"
            ) from exc

    def _validate_draft(
        self,
        credential: VerifiableCredential,
    ) -> None:
        if credential.status != CredentialStatus.DRAFT:
            raise CredentialInvalidDataError(
                "Only draft credentials can be issued."
            )

        # Revalidate the organization and issuer DID.
        did = self._get_verified_issuer_did(
            credential.organization_id
        )

        if did.id != credential.issuer_did_id:
            raise CredentialInvalidDataError(
                "Credential issuer does not match the organization's verified DID."
            )

    # ---------------------------------------------------------
    # Draft creation
    # ---------------------------------------------------------

    def create_draft(
        self,
        organization_id: UUID,
        data: CredentialCreate,
    ) -> VerifiableCredential:

        did = self._get_verified_issuer_did(
            organization_id
        )

        now = datetime.now(timezone.utc)

        valid_until = data.valid_until

        if valid_until is not None:
            if (
                valid_until.tzinfo is None
                or valid_until.utcoffset() is None
            ):
                raise CredentialInvalidDataError(
                    "valid_until must include a timezone."
                )

            if valid_until <= now:
                raise CredentialInvalidDataError(
                    "valid_until must be in the future."
                )

        credential_type = data.credential_type.strip()

        if (
            not credential_type
            or credential_type == "VerifiableCredential"
        ):
            raise CredentialInvalidDataError(
                "A specific credential type is required."
            )

        if not data.subject:
            raise CredentialInvalidDataError(
                "Credential subject cannot be empty."
            )

        credential_uuid = uuid4()
        credential_identifier = f"urn:uuid:{credential_uuid}"

        credential_types = [
            "VerifiableCredential",
            credential_type,
        ]

        payload = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
            ],
            "id": credential_identifier,
            "type": credential_types,
            "issuer": did.identifier,
            "validFrom": now.isoformat(),
            "credentialSubject": data.subject,
        }

        if valid_until is not None:
            payload["validUntil"] = valid_until.isoformat()

        credential = VerifiableCredential(
            id=credential_uuid,
            credential_id=credential_identifier,
            organization_id=organization_id,
            issuer_did_id=did.id,
            credential_type=credential_type,
            credential_subject=data.subject,
            payload=payload,
            proof=None,
            status=CredentialStatus.DRAFT,
            valid_from=now,
            valid_until=valid_until,
        )

        try:
            return self.repository.create(credential)

        except IntegrityError as exc:
            self.session.rollback()

            raise CredentialAlreadyExistsError(
                "Credential identifier already exists."
            ) from exc

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def get(
        self,
        credential_id: UUID,
    ) -> VerifiableCredential | None:
        return self.repository.get_by_id(credential_id)

    def list_by_organization(
        self,
        organization_id: UUID,
    ) -> list[VerifiableCredential]:
        return self.repository.list_by_organization(
            organization_id
        )

    # ---------------------------------------------------------
    # Issuer signing key resolution
    # ---------------------------------------------------------

    def get_issuer_signing_key(
        self,
        credential_id: UUID,
    ) -> tuple[str, str]:

        credential = self._get_credential_or_raise(
            credential_id
        )

        self._validate_draft(credential)

        return self._get_issuer_key(credential)

    # ---------------------------------------------------------
    # Prepare issuance
    # ---------------------------------------------------------

    def prepare_issuance(
        self,
        credential_id: UUID,
    ) -> dict:

        credential = self._get_credential_or_raise(
            credential_id
        )

        self._validate_draft(credential)

        key_id, _public_key = self._get_issuer_key(
            credential
        )

        signing_input = build_signing_input(
            credential.payload,
            key_id,
        )

        return {
            "signing_input": signing_input,
            "key_id": key_id,
        }

    # ---------------------------------------------------------
    # Complete issuance
    # ---------------------------------------------------------

    def complete_issuance(
        self,
        credential_id: UUID,
        signature: str,
        key_id: str,
    ) -> VerifiableCredential:

        credential = self._get_credential_or_raise(
            credential_id
        )

        self._validate_draft(credential)

        expected_key_id, public_key = self._get_issuer_key(
            credential
        )

        if key_id != expected_key_id:
            raise CredentialInvalidDataError(
                "Signing key does not belong to this issuer."
            )

        signing_input = build_signing_input(
            credential.payload,
            expected_key_id,
        )

        try:
            signed_credential = complete_jws(
                signing_input,
                signature,
            )

            verify_jws(
                signed_credential,
                public_key,
                expected_key_id,
            )

        except JWSVerificationError as exc:
            raise CredentialInvalidDataError(
                f"Credential signature verification failed: {exc}"
            ) from exc

        credential.signed_credential = signed_credential

        credential.proof = {
            "verificationMethod": expected_key_id,
            "algorithm": "ES256K",
        }

        credential.status = CredentialStatus.ISSUED

        try:
            self.session.commit()
            self.session.refresh(credential)

        except IntegrityError as exc:
            self.session.rollback()

            raise CredentialInvalidDataError(
                "Unable to persist issued credential."
            ) from exc

        return credential