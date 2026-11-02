
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keepyourid.modules.credentials.enums import CredentialStatus
from keepyourid.modules.credentials.models import VerifiableCredential
from keepyourid.modules.credentials.repository import CredentialRepository
from keepyourid.modules.credentials.schemas import CredentialCreate
from keepyourid.modules.dids.enums import DIDStatus
from keepyourid.modules.dids.models import DID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization
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
		organization = self.session.get(Organization, organization_id)

		if organization is None:
			raise CredentialOrganizationNotFoundError(
				"Organization not found."
			)

		if organization.status != OrganizationStatus.ACTIVE:
			raise CredentialOrganizationInactiveError(
				"Organization must be active to issue credentials."
			)

		statement_did = self.session.query(DID).filter(
			DID.organization_id == organization_id
		)
		did = statement_did.first()

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

		credential_uuid = uuid4()
		credential_identifier = f"urn:uuid:{credential_uuid}"

		credential_types = [
			"VerifiableCredential",
			data.credential_type.strip(),
		]

		if (
			not data.credential_type.strip()
			or data.credential_type.strip() == "VerifiableCredential"
		):
			raise CredentialInvalidDataError(
				"A specific credential type is required."
			)

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

		if data.valid_until is not None:
			payload["validUntil"] = data.valid_until.isoformat()

		credential = VerifiableCredential(
			id=credential_uuid,
			credential_id=credential_identifier,
			organization_id=organization_id,
			issuer_did_id=did.id,
			credential_type=data.credential_type.strip(),
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

	def get(self, credential_id: UUID) -> VerifiableCredential | None:
		return self.repository.get_by_id(credential_id)

	def list_by_organization(
		self,
		organization_id: UUID,
	) -> list[VerifiableCredential]:
		return self.repository.list_by_organization(organization_id)

	def _get_issuer_key_id(
		self,
		credential: VerifiableCredential,
	) -> str:
		try:
			key_id, _ = IssuerKeyResolver(self.session).resolve(
				credential
			)
			return key_id
		except IssuerKeyError as exc:
			raise CredentialInvalidDataError(str(exc)) from exc


	def _get_issuer_public_key(
		self,
		credential: VerifiableCredential,
	) -> str:
		try:
			_, public_key = IssuerKeyResolver(self.session).resolve(
				credential
			)
			return public_key
		except IssuerKeyError as exc:
			raise CredentialInvalidDataError(str(exc)) from exc
	
	def prepare_issuance(self, credential_id: UUID):
		credential = self.get(credential_id)

		if credential is None:
			raise CredentialInvalidDataError("Credential not found.")

		if credential.status != CredentialStatus.DRAFT:
			raise CredentialInvalidDataError(
				"Only draft credentials can be issued."
			)

		key_id = self._get_issuer_key_id(credential)

		return {
			"signing_input": build_signing_input(
				credential.payload,
				key_id,
			),
			"key_id": key_id,
		}


	def complete_issuance(
		self,
		credential_id: UUID,
		signature: str,
		key_id: str,
	):
		credential = self.get(credential_id)

		if credential is None:
			raise CredentialInvalidDataError("Credential not found.")

		if credential.status != CredentialStatus.DRAFT:
			raise CredentialInvalidDataError(
				"Only draft credentials can be issued."
			)

		expected_key_id = self._get_issuer_key_id(credential)

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

			public_key = self._get_issuer_public_key(credential)

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
			"type": "JsonWebSignature2020",
			"format": "vc+jwt",
			"verificationMethod": expected_key_id,
			"algorithm": "ES256K",
		}
		credential.status = CredentialStatus.ISSUED

		self.session.commit()
		self.session.refresh(credential)

		return credential

	def get_issuer_signing_key(self, credential_id: UUID):
		credential = self.get(credential_id)

		if credential is None:
			raise CredentialInvalidDataError("Credential not found.")

		try:
			return IssuerKeyResolver(self.session).resolve(credential)
		except IssuerKeyError as exc:
			raise CredentialInvalidDataError(str(exc)) from exc


	
