from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keepyourid.modules.credentials.enums import CredentialStatus
from keepyourid.modules.credentials.models import VerifiableCredential
from keepyourid.modules.credentials.repository import CredentialRepository
from keepyourid.modules.credentials.schemas import CredentialCreate
from keepyourid.modules.credentials.cryptography.jws import (
    build_signing_input,
    complete_jws,
    verify_jws,
    JWSVerificationError,
)
from keepyourid.modules.credentials.cryptography.issuer_keys import (
    IssuerKeyResolver,
    IssuerKeyError,
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

    def create_draft(
        self,
        organization_id: UUID,
        data: CredentialCreate,
    ) -> VerifiableCredential:

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

        now = datetime.now(timezone.utc)

        if data.valid_until is not None:
            if data.valid_until.tzinfo is None:
                raise CredentialInvalidDataError(
                    "valid_until must include a timezone."
                )

            if data.valid_until <= now:
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

        credential_uuid = uuid4()
        credential_identifier = f"urn:uuid:{credential_uuid}"

        payload = {
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
            ],
            "id": credential_identifier,
            "type": [
                "VerifiableCredential",
                credential_type,
            ],
            "issuer": did.identifier,
            "validFrom": now.isoformat(),
            "credentialSubject": data.subject,
        }

        if data.valid_until is not None:
            payload["validUntil"] = data.valid_until.isoformat()

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
            valid_until=data.valid_until,
        )

        try:
            return self.repository.create(credential)

        except IntegrityError as exc:
            self.session.rollback()

            raise CredentialAlreadyExistsError(
                "Credential identifier already exists."
            ) from exc

    def get(
        self,
        credential_id: UUID,
        organization_id: UUID | None = None,
    ) -> VerifiableCredential | None:

        credential = self.repository.get_by_id(credential_id)

        if credential is None:
            return None

        if organization_id is not None and credential.organization_id != organization_id:
            return None

        return credential

    def list_by_organization(
        self,
        organization_id: UUID,
    ) -> list[VerifiableCredential]:

        return self.repository.list_by_organization(
            organization_id
        )

    # ---------------------------------------------------------
    # Issuer key resolution
    # ---------------------------------------------------------

    def _resolve_issuer_key(
        self,
        credential: VerifiableCredential,
    ) -> tuple[str, str]:
        """
        Resolves the issuer's authorized assertion key.

        Returns:
            (key_id, public_key_hex)
        """

        try:
            return IssuerKeyResolver(
                self.session
            ).resolve(credential)

        except IssuerKeyError as exc:
            raise CredentialInvalidDataError(
                str(exc)
            ) from exc

    def _get_issuer_key_id(
        self,
        credential: VerifiableCredential,
    ) -> str:

        key_id, _ = self._resolve_issuer_key(credential)
        return key_id

    def _get_issuer_public_key(
        self,
        credential: VerifiableCredential,
    ) -> str:

        _, public_key = self._resolve_issuer_key(credential)
        return public_key

    # ---------------------------------------------------------
    # Credential issuance preparation
    # ---------------------------------------------------------

    def prepare_issuance(
        self,
        credential_id: UUID,
        organization_id: UUID | None = None,
    ) -> dict:

        credential = self.get(credential_id, organization_id)

        if credential is None:
            raise CredentialInvalidDataError(
                "Credential not found."
            )

        if credential.status != CredentialStatus.DRAFT:
            raise CredentialInvalidDataError(
                "Only draft credentials can be issued."
            )

        key_id, _ = self._resolve_issuer_key(credential)

        try:
            signing_input = build_signing_input(
                credential.payload,
                key_id,
            )

        except JWSVerificationError as exc:
            raise CredentialInvalidDataError(
                f"Unable to prepare credential signing: {exc}"
            ) from exc

        return {
            "signing_input": signing_input,
            "key_id": key_id,
        }

    # ---------------------------------------------------------
    # Credential issuance completion
    # ---------------------------------------------------------

    def complete_issuance(
        self,
        credential_id: UUID,
        signature: str,
        key_id: str,
        organization_id: UUID | None = None,
    ) -> VerifiableCredential:

        statement = (
            select(VerifiableCredential)
            .where(VerifiableCredential.id == credential_id)
            .with_for_update()
        )
        credential = self.session.scalar(statement)

        if credential is None:
            raise CredentialInvalidDataError(
                "Credential not found."
            )

        if (
            organization_id is not None
            and credential.organization_id != organization_id
        ):
            raise CredentialInvalidDataError(
                "Credential not found."
            )

        if credential.status != CredentialStatus.DRAFT:
            raise CredentialInvalidDataError(
                "Only draft credentials can be issued."
            )

        expected_key_id, public_key = self._resolve_issuer_key(
            credential
        )

        if key_id != expected_key_id:
            raise CredentialInvalidDataError(
                "Signing key does not belong to this issuer."
            )

        try:
            signing_input = build_signing_input(
                credential.payload,
                expected_key_id,
            )

            signed_credential = complete_jws(
                signing_input,
                signature,
            )

            verified_payload = verify_jws(
                signed_credential,
                public_key,
                expected_key_id,
            )

            if verified_payload != credential.payload:
                raise JWSVerificationError(
                    "Signed credential payload does not match stored credential."
                )

        except JWSVerificationError as exc:
            raise CredentialInvalidDataError(
                f"Credential signature verification failed: {exc}"
            ) from exc

        credential.signed_credential = signed_credential

        # The credential is represented by a compact JWS.
        # Do not mislabel it as JsonWebSignature2020.
        credential.proof = None

        credential.status = CredentialStatus.ISSUED

        try:
            self.session.commit()
            self.session.refresh(credential)

        except Exception:
            self.session.rollback()
            raise

        return credential

    # ---------------------------------------------------------
    # Issuer signing key information
    # ---------------------------------------------------------

    def get_issuer_signing_key(
        self,
        credential_id: UUID,
        organization_id: UUID | None = None,
    ) -> tuple[str, str]:

        credential = self.get(credential_id, organization_id)

        if credential is None:
            raise CredentialInvalidDataError(
                "Credential not found."
            )

        return self._resolve_issuer_key(credential)

    def revoke(
        self,
        credential_id: UUID,
        reason: str | None = None,
        organization_id: UUID | None = None,
    ) -> VerifiableCredential:
        credential = self.get(credential_id, organization_id)

        if credential is None:
            raise CredentialInvalidDataError("Credential not found.")

        if credential.status == CredentialStatus.REVOKED:
            return credential

        credential.status = CredentialStatus.REVOKED
        payload = dict(credential.proof or {})
        payload["revoked"] = True
        if reason:
            payload["reason"] = reason
        credential.proof = payload

        try:
            self.session.commit()
            self.session.refresh(credential)
        except Exception:
            self.session.rollback()
            raise

        return credential