import json
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

from keepyourid_verifier.engine import CredentialVerifier


class CredentialVerificationValidationError(Exception):
    pass


class CredentialVerificationEngineError(Exception):
    pass


class CredentialVerificationService:
    def __init__(
        self,
        verifier: CredentialVerifier | None = None,
        allowed_status_list_hosts: Iterable[str] | str | None = None,
    ):
        self.verifier = verifier if verifier is not None else CredentialVerifier()
        self.allowed_status_list_hosts = self._normalize_hosts(
            allowed_status_list_hosts
        )

    @staticmethod
    def _normalize_hosts(
        allowed_status_list_hosts: Iterable[str] | str | None,
    ) -> frozenset[str]:
        if allowed_status_list_hosts is None:
            return frozenset()

        if isinstance(allowed_status_list_hosts, str):
            values = allowed_status_list_hosts.split(",")
        else:
            values = allowed_status_list_hosts

        return frozenset(
            value.strip().lower()
            for value in values
            if value.strip()
        )

    def verify(self, signed_credential: dict[str, Any] | str) -> dict[str, Any]:
        envelope = self._load_envelope(signed_credential)
        credential = envelope["credential"]
        proof = envelope["proof"]

        self._validate_credential_fields(credential)
        self._validate_proof_fields(proof)
        self._validate_status_list_destinations(credential)

        try:
            result = self.verifier.verify(envelope)
            return result.to_dict()
        except Exception as exc:
            raise CredentialVerificationEngineError(
                "Credential verification failed unexpectedly."
            ) from exc

    def _load_envelope(
        self,
        signed_credential: dict[str, Any] | str,
    ) -> dict[str, Any]:
        if isinstance(signed_credential, str):
            if not signed_credential.strip():
                raise CredentialVerificationValidationError(
                    "signed_credential must not be empty."
                )

            try:
                envelope = json.loads(signed_credential)
            except json.JSONDecodeError as exc:
                raise CredentialVerificationValidationError(
                    "signed_credential must be valid JSON."
                ) from exc
        elif isinstance(signed_credential, dict):
            envelope = signed_credential
        else:
            raise CredentialVerificationValidationError(
                "signed_credential must be a JSON object or JSON string."
            )

        if not isinstance(envelope, dict):
            raise CredentialVerificationValidationError(
                "signed_credential must be a JSON object."
            )

        credential = envelope.get("credential")
        proof = envelope.get("proof")

        if not isinstance(credential, dict) or not isinstance(proof, dict):
            raise CredentialVerificationValidationError(
                "signed_credential must contain credential and proof objects."
            )

        return envelope

    def _validate_credential_fields(self, credential: dict[str, Any]) -> None:
        credential_id = credential.get("id")
        if credential_id is not None and not isinstance(credential_id, str):
            raise CredentialVerificationValidationError(
                "credential.id must be a string."
            )

        issuer = credential.get("issuer")
        if issuer is not None and not isinstance(issuer, str):
            raise CredentialVerificationValidationError(
                "credential.issuer must be a string."
            )

        for field in ("validFrom", "validUntil"):
            value = credential.get(field)
            if value is not None and not isinstance(value, str):
                raise CredentialVerificationValidationError(
                    f"credential.{field} must be a string."
                )

    def _validate_proof_fields(self, proof: dict[str, Any]) -> None:
        if proof.get("type") != "Eip191PersonalSignature":
            return

        for field in ("signature", "verificationMethod", "signer"):
            value = proof.get(field)
            if value is not None and not isinstance(value, str):
                raise CredentialVerificationValidationError(
                    f"proof.{field} must be a string."
                )

    def _validate_status_list_destinations(
        self,
        credential: dict[str, Any],
    ) -> None:
        credential_status = credential.get("credentialStatus")
        if credential_status is None:
            return

        entries = (
            credential_status
            if isinstance(credential_status, list)
            else [credential_status]
        )

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            if entry.get("statusPurpose") != "revocation":
                continue

            if entry.get("type") != "BitstringStatusListEntry":
                continue

            if "statusListCredential" not in entry:
                continue

            status_list_url = entry.get("statusListCredential")

            if not isinstance(status_list_url, str) or not self._is_allowed_url(
                status_list_url
            ):
                raise CredentialVerificationValidationError(
                    "Status list destination is not allowed."
                )

    def _is_allowed_url(self, url: str) -> bool:
        if not self.allowed_status_list_hosts:
            return False

        try:
            parsed = urlparse(url)
        except ValueError:
            return False

        if parsed.scheme.lower() not in {"http", "https"}:
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        hostname = hostname.lower()
        netloc = parsed.netloc.lower()

        return any(
            hostname == allowed or netloc == allowed
            for allowed in self.allowed_status_list_hosts
        )
