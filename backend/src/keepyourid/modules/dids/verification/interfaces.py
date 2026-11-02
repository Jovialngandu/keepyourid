from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ResolvedDID:
    did: str
    document: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    did: str
    signer_address: str
    verification_method: str
    reason: str | None = None


class DIDResolver(Protocol):
    def resolve(self, did: str) -> ResolvedDID:
        ...


class DIDMethodVerifier(Protocol):
    def validate_did_document(
        self,
        did: str,
        document: dict[str, Any],
    ) -> None:
        ...


class SignatureVerifier(Protocol):
    def recover_signer(
        self,
        message: str,
        signature: str,
    ) -> str:
        ...