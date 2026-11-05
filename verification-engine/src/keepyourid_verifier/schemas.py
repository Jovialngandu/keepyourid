
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerificationResult:
    valid: bool
    credential_id: str | None
    issuer: str | None
    checks: dict[str, bool | None] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "credential_id": self.credential_id,
            "issuer": self.issuer,
            "checks": self.checks,
            "errors": self.errors,
        }
