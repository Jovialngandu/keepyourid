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
from keepyourid.modules.holders.models import HolderDID
from keepyourid.modules.organizations.enums import OrganizationStatus
from keepyourid.modules.organizations.models import Organization

import json

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_checksum_address
from keepyourid.modules.credentials.status_list_model import (
    CredentialStatusList,
)

import base64
import gzip

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

		holder_did: HolderDID | None = None
		if data.holder_did_id is not None:
			holder_did = self.session.get(HolderDID, data.holder_did_id)
			if holder_did is None:
				raise CredentialInvalidDataError("Holder DID not found.")

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
			holder_did_id=data.holder_did_id,
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

	def list_by_holder_user(
		self,
		user_id: UUID,
	) -> list[VerifiableCredential]:
		return self.repository.list_by_holder_user(user_id)

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
		status_list_url: str | None = None,
	) -> dict:
		credential = self.get(credential_id, organization_id)

		if credential is None:
			raise CredentialInvalidDataError("Credential not found.")

		if credential.status != CredentialStatus.DRAFT:
			raise CredentialInvalidDataError(
				"Only draft credentials can be issued."
			)

		if not status_list_url:
			raise CredentialInvalidDataError(
				"Status list URL is required."
			)

		key_id, issuer_address = self._resolve_issuer_key(credential)

		issuer_did = self.session.get(DID, credential.issuer_did_id)

		if issuer_did is None:
			raise CredentialInvalidDataError("Issuer DID not found.")

		statement = (
			select(CredentialStatusList)
			.where(
				CredentialStatusList.issuer_did_id
				== credential.issuer_did_id
			)
			.with_for_update()
		)
		status_list = self.session.scalar(statement)

		if status_list is None:
			status_list = CredentialStatusList(
				issuer_did_id=credential.issuer_did_id,
				bitstring=bytes(16 * 1024),
				next_index=0,
			)
			self.session.add(status_list)
			self.session.flush()

		if credential.status_list_index is None:
			index = status_list.next_index

			if index >= len(status_list.bitstring) * 8:
				raise CredentialInvalidDataError(
					"Status list capacity exceeded."
				)

			credential.status_list_index = index
			status_list.next_index = index + 1

		index = credential.status_list_index

		credential.payload = {
			**credential.payload,
			"credentialStatus": {
				"id": f"{status_list_url}#{index}",
				"type": "BitstringStatusListEntry",
				"statusPurpose": "revocation",
				"statusListIndex": str(index),
				"statusListCredential": status_list_url,
			},
		}

		status_payload = self._build_status_list_payload(
			status_list,
			issuer_did,
			status_list_url,
			valid_from=credential.payload["validFrom"],
		)

		credential_signing_input = build_signing_input(
			credential.payload,
			key_id,
		)

		status_list_signing_input = build_signing_input(
			status_payload,
			key_id,
		)

		try:
			self.session.commit()
		except Exception:
			self.session.rollback()
			raise

		return {
			"signing_input": credential_signing_input,
			"key_id": key_id,
			"issuer_address": issuer_address,
			"status_list_signing_input": status_list_signing_input,
			"status_list_url": status_list_url,
			"status_list_index": index,
		}

	# ---------------------------------------------------------
	# Credential issuance completion
	# ---------------------------------------------------------

	def complete_issuance(
		self,
		credential_id: UUID,
		signature: str,
		key_id: str,
		status_list_signature: str,
		organization_id: UUID | None = None,
	) -> VerifiableCredential:

		statement = (
			select(VerifiableCredential)
			.where(VerifiableCredential.id == credential_id)
			.with_for_update()
		)
		credential = self.session.scalar(statement)

		if credential is None:
			raise CredentialInvalidDataError("Credential not found.")

		if (
			organization_id is not None
			and credential.organization_id != organization_id
		):
			raise CredentialInvalidDataError("Credential not found.")

		if credential.status != CredentialStatus.DRAFT:
			raise CredentialInvalidDataError(
				"Only draft credentials can be issued."
			)

		if credential.status_list_index is None:
			raise CredentialInvalidDataError(
				"Credential has no reserved status list index."
			)

		expected_key_id, issuer_address = self._resolve_issuer_key(credential)

		if key_id != expected_key_id:
			raise CredentialInvalidDataError(
				"Signing key does not belong to this issuer."
			)

		try:
			credential_proof = self._make_issuer_proof(
				credential.payload,
				expected_key_id,
				signature,
				issuer_address,
			)

			status_url = credential.payload["credentialStatus"][
				"statusListCredential"
			]

			status_list = self.session.scalar(
				select(CredentialStatusList)
				.where(
					CredentialStatusList.issuer_did_id
					== credential.issuer_did_id
				)
				.with_for_update()
			)

			issuer_did = self.session.get(DID, credential.issuer_did_id)

			if status_list is None or issuer_did is None:
				raise CredentialInvalidDataError(
					"Issuer status list not found."
				)

			status_payload = self._build_status_list_payload(
				status_list,
				issuer_did,
				status_url,
				valid_from=credential.payload["validFrom"],
			)

			status_proof = self._make_issuer_proof(
				status_payload,
				expected_key_id,
				status_list_signature,
				issuer_address,
			)

		except CredentialInvalidDataError:
			raise
		except Exception as exc:
			raise CredentialInvalidDataError(
				f"Issuance signature verification failed: {exc}"
			) from exc

		credential.proof = credential_proof
		credential.signed_credential = json.dumps(
			{
				"credential": credential.payload,
				"proof": credential_proof,
			},
			ensure_ascii=False,
		)

		status_list.proof = status_proof
		status_list.signed_credential = json.dumps(
			{
				"credential": status_payload,
				"proof": status_proof,
			},
			ensure_ascii=False,
		)

		credential.status = CredentialStatus.ISSUED

		try:
			self.session.commit()
			self.session.refresh(credential)
		except Exception:
			self.session.rollback()
			raise

		return credential	# ---------------------------------------------------------
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

	def prepare_revocation(
		self,
		credential_id: UUID,
		organization_id: UUID | None = None,
	) -> dict:
		credential = self.get(credential_id, organization_id)

		if credential is None:
			raise CredentialInvalidDataError("Credential not found.")

		if credential.status != CredentialStatus.ISSUED:
			raise CredentialInvalidDataError(
				"Only issued credentials can be revoked."
			)

		if credential.status_list_index is None:
			raise CredentialInvalidDataError("Credential has no status list index.")

		status_url = credential.payload["credentialStatus"]["statusListCredential"]

		status_list = self.session.scalar(
			select(CredentialStatusList).where(
				CredentialStatusList.issuer_did_id == credential.issuer_did_id
			)
		)
		issuer_did = self.session.get(DID, credential.issuer_did_id)

		if status_list is None or not status_list.signed_credential or issuer_did is None:
			raise CredentialInvalidDataError("Issuer status list not found.")

		previous = json.loads(status_list.signed_credential)
		valid_from = previous["credential"]["validFrom"]

		updated_bitstring = self._revoked_bitstring(
			status_list.bitstring,
			credential.status_list_index,
		)

		payload = self._build_status_list_payload(
			status_list,
			issuer_did,
			status_url,
			valid_from,
			bitstring=updated_bitstring,
		)

		key_id, _ = self._resolve_issuer_key(credential)

		return {
			"signing_input": build_signing_input(payload, key_id),
			"key_id": key_id,
			"status_list_url": status_url,
			"status_list_index": credential.status_list_index,
		}


	def complete_revocation(
		self,
		credential_id: UUID,
		signature: str,
		key_id: str,
		organization_id: UUID | None = None,
	) -> VerifiableCredential:
		credential = self.session.scalar(
			select(VerifiableCredential)
			.where(VerifiableCredential.id == credential_id)
			.with_for_update()
		)

		if credential is None or (
			organization_id is not None
			and credential.organization_id != organization_id
		):
			raise CredentialInvalidDataError("Credential not found.")

		if credential.status != CredentialStatus.ISSUED:
			raise CredentialInvalidDataError("Only issued credentials can be revoked.")

		if credential.status_list_index is None:
			raise CredentialInvalidDataError("Credential has no status list index.")

		expected_key_id, issuer_address = self._resolve_issuer_key(credential)

		if key_id != expected_key_id:
			raise CredentialInvalidDataError("Signing key does not belong to this issuer.")

		status_list = self.session.scalar(
			select(CredentialStatusList)
			.where(CredentialStatusList.issuer_did_id == credential.issuer_did_id)
			.with_for_update()
		)
		issuer_did = self.session.get(DID, credential.issuer_did_id)

		if status_list is None or not status_list.signed_credential or issuer_did is None:
			raise CredentialInvalidDataError("Issuer status list not found.")

		status_url = credential.payload["credentialStatus"]["statusListCredential"]
		previous = json.loads(status_list.signed_credential)
		valid_from = previous["credential"]["validFrom"]

		updated_bitstring = self._revoked_bitstring(
			status_list.bitstring,
			credential.status_list_index,
		)

		status_payload = self._build_status_list_payload(
			status_list,
			issuer_did,
			status_url,
			valid_from,
			bitstring=updated_bitstring,
		)

		try:
			status_proof = self._make_issuer_proof(
				status_payload,
				expected_key_id,
				signature,
				issuer_address,
			)
		except Exception as exc:
			raise CredentialInvalidDataError(
				f"Revocation signature verification failed: {exc}"
			) from exc

		# Publication du nouveau Status List et révocation en une transaction.
		status_list.bitstring = updated_bitstring
		status_list.proof = status_proof
		status_list.signed_credential = json.dumps(
			{"credential": status_payload, "proof": status_proof},
			ensure_ascii=False,
		)
		credential.status = CredentialStatus.REVOKED

		try:
			self.session.commit()
			self.session.refresh(credential)
		except Exception:
			self.session.rollback()
			raise

		return credential

	def _encode_status_bitstring(self, bitstring: bytes) -> str:
		compressed = gzip.compress(bitstring, mtime=0)
		encoded = base64.urlsafe_b64encode(compressed)
		return "u" + encoded.rstrip(b"=").decode("ascii")

	def _build_status_list_payload(
		self,
		status_list: CredentialStatusList,
		issuer_did: DID,
		status_list_url: str,
		valid_from: str,
		bitstring: bytes | None = None,
	) -> dict:
		return {
			"@context": ["https://www.w3.org/ns/credentials/v2"],
			"id": status_list_url,
			"type": [
				"VerifiableCredential",
				"BitstringStatusListCredential",
			],
			"issuer": issuer_did.identifier,
			"validFrom": valid_from,
			"credentialSubject": {
				"id": f"{status_list_url}#list",
				"type": "BitstringStatusList",
				"statusPurpose": "revocation",
				"encodedList": self._encode_status_bitstring(
					bitstring if bitstring is not None else status_list.bitstring
				),
			},
		}

	def _make_issuer_proof(
		self,
		payload: dict,
		key_id: str,
		signature: str,
		issuer_address: str,
	) -> dict:
		signing_input = build_signing_input(payload, key_id)
		recovered_address = Account.recover_message(
			encode_defunct(text=signing_input),
			signature=signature,
		)

		if (
			to_checksum_address(recovered_address)
			!= to_checksum_address(issuer_address)
		):
			raise CredentialInvalidDataError(
				"Signature does not belong to the issuer DID."
			)

		return {
			"type": "Eip191PersonalSignature",
			"verificationMethod": key_id,
			"signer": issuer_address,
			"signature": signature,
		}
  
	def _revoked_bitstring(self, bitstring: bytes, index: int) -> bytes:
		data = bytearray(bitstring)
		byte_index = index // 8

		if byte_index >= len(data):
			raise CredentialInvalidDataError("Status list index is out of range.")

		data[byte_index] |= 1 << (7 - index % 8)
		return bytes(data)