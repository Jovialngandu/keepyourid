from dataclasses import dataclass
from typing import Any


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