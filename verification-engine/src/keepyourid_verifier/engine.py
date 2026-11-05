
import json
from typing import Any

from keepyourid_verifier.checks.signature import verify_signature
from keepyourid_verifier.checks.issuer import verify_issuer
from keepyourid_verifier.checks.expiration import verify_expiration
from keepyourid_verifier.schemas import VerificationResult
from keepyourid_verifier.checks.issuer_trust import verify_issuer_trust
from keepyourid_verifier.checks.revocation import verify_revocation

import os

class CredentialVerifier:

	def __init__(self):
		self.rpc_url = os.getenv("ISSUER_REGISTRY_RPC_URL")
		self.registry_address = os.getenv("ISSUER_REGISTRY_ADDRESS")

	def verify(
		self,
		signed_credential: str | dict[str, Any],
	) -> VerificationResult:

		try:
			envelope = (
				json.loads(signed_credential)
				if isinstance(signed_credential, str)
				else signed_credential
			)
		except (json.JSONDecodeError, TypeError):
			return VerificationResult(
				valid=False,
				credential_id=None,
				issuer=None,
				errors=["Invalid signed credential JSON."],
			)

		if not isinstance(envelope, dict):
			return VerificationResult(
				valid=False,
				credential_id=None,
				issuer=None,
				errors=["Invalid credential envelope."],
			)

		credential = envelope.get("credential")
		proof = envelope.get("proof")

		if not isinstance(credential, dict) or not isinstance(proof, dict):
			return VerificationResult(
				valid=False,
				credential_id=None,
				issuer=None,
				errors=["Credential or proof is missing."],
			)

		credential_id = credential.get("id")
		issuer = credential.get("issuer")
		errors = []

		if proof.get("type") != "Eip191PersonalSignature":
			return VerificationResult(
				valid=False,
				credential_id=credential_id,
				issuer=issuer,
				errors=["Unsupported proof type."],
			)

		signature_valid, recovered_address = verify_signature(
			credential,
			proof,
		)

		issuer_valid = verify_issuer(
			issuer or "",
			recovered_address,
		)

		expiration_valid, expiration_error = verify_expiration(
			credential
		)

		if not signature_valid:
			errors.append("Credential signature is invalid.")

		if not issuer_valid:
			errors.append("Signer does not match the issuer DID.")

		if expiration_error:
			errors.append(expiration_error)
			
		revocation_valid, revocation_error = verify_revocation(
			credential
		)

		if revocation_error:
			errors.append(revocation_error)
			
		issuer_trust_valid, issuer_trust_error = verify_issuer_trust(
		issuer_did=issuer or "",
		rpc_url=self.rpc_url or "",
		registry_address=self.registry_address or "",
		)

		if issuer_trust_error:
			errors.append(issuer_trust_error)
  
		checks = {
			"signature": signature_valid,
			"issuer_did": issuer_valid,
			"issuer_trust": issuer_trust_valid,
			"revocation": revocation_valid,
			"expiration": expiration_valid,
		}


		# Never report VALID while mandatory checks remain unimplemented.
		valid = all(value is True for value in checks.values())

		return VerificationResult(
			valid=valid,
			credential_id=credential_id,
			issuer=issuer,
			checks=checks,
			errors=errors,
		)
