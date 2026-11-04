
from datetime import datetime, timezone

from keepyourid.verification.did_ethr import (
    DIDDocumentValidationError,
    DIDEthrVerifier,
)
from keepyourid.verification.interfaces import DIDResolver
from keepyourid.verification.did.resolver import (
    DIDResolutionError,
)
from keepyourid.verification.did.signature import (
    EthereumSignatureVerifier,
    SignatureVerificationError,
    build_authentication_message,
)


class DIDVerificationError(Exception):
    pass


class DIDVerificationService:
    def __init__(
        self,
        resolver: DIDResolver | None = None,
        method_verifier: DIDEthrVerifier | None = None,
        signature_verifier: EthereumSignatureVerifier | None = None,
    ):
        self.resolver = resolver
        self.method_verifier = method_verifier or DIDEthrVerifier()
        self.signature_verifier = (
            signature_verifier or EthereumSignatureVerifier()
        )

    def verify_authentication(
        self,
        *,
        did: str,
        challenge: str,
        purpose: str,
        domain: str,
        issued_at: datetime,
        expires_at: datetime,
        verification_method: str,
        signature: str,
        did_document: dict | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)

        if issued_at.tzinfo is None or expires_at.tzinfo is None:
            raise DIDVerificationError(
                "Challenge timestamps must be timezone-aware."
            )

        if issued_at > now or expires_at <= now:
            raise DIDVerificationError(
                "Challenge is not currently valid."
            )

        if not challenge or not purpose or not domain:
            raise DIDVerificationError(
                "Challenge context is incomplete."
            )

        try:
            # Use the locally stored document when provided.
            # Otherwise, fall back to the configured resolver.
            if did_document is None:
                if self.resolver is None:
                    raise DIDVerificationError(
                        "No DID document or resolver available."
                    )

                resolved = self.resolver.resolve(did)
                did_document = resolved.document

            self.method_verifier.validate_did_document(
                did,
                did_document,
            )

            method_id, expected_address = (
                self.method_verifier.get_authorized_method(
                    did,
                    did_document,
                    verification_method,
                )
            )

            message = build_authentication_message(
                did=did,
                challenge=challenge,
                purpose=purpose,
                domain=domain,
                issued_at=issued_at.isoformat(),
                expires_at=expires_at.isoformat(),
            )

            signer_address = self.signature_verifier.recover_signer(
                message,
                signature,
            )

            if signer_address.lower() != expected_address.lower():
                raise DIDVerificationError(
                    "Signature does not match the authorized DID key."
                )

            return {
                "valid": True,
                "did": did,
                "signer_address": signer_address,
                "verification_method": method_id,
            }

        except (
            DIDResolutionError,
            DIDDocumentValidationError,
            SignatureVerificationError,
        ) as exc:
            raise DIDVerificationError(str(exc)) from exc
