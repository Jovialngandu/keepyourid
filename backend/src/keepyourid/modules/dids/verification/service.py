
from datetime import datetime, timezone

from keepyourid.modules.dids.verification.did_ethr import (
    DIDDocumentValidationError,
    DIDEthrVerifier,
)
from keepyourid.modules.dids.verification.interfaces import DIDResolver
from keepyourid.modules.dids.verification.resolver import (
    DIDResolutionError,
)
from keepyourid.modules.dids.verification.signature import (
    EthereumSignatureVerifier,
    SignatureVerificationError,
    build_authentication_message,
)


class DIDVerificationError(Exception):
    pass


class DIDVerificationService:
    def __init__(
        self,
        resolver: DIDResolver,
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
            resolved = self.resolver.resolve(did)

            self.method_verifier.validate_did_document(
                did,
                resolved.document,
            )

            method_id, expected_address = (
                self.method_verifier.get_authorized_method(
                    did,
                    resolved.document,
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
