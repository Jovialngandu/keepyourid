import json
from typing import Any

from pydantic import BaseModel, Field, model_validator

MAX_SIGNED_CREDENTIAL_BYTES = 256 * 1024


class CredentialVerificationRequest(BaseModel):
    signed_credential: dict[str, Any] | str

    @model_validator(mode="after")
    def validate_size(self):
        value = self.signed_credential

        if isinstance(value, str):
            size = len(value.encode("utf-8"))
        else:
            size = len(
                json.dumps(
                    value,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            )

        if size > MAX_SIGNED_CREDENTIAL_BYTES:
            raise ValueError("signed_credential is too large.")

        return self


class CredentialVerificationResponse(BaseModel):
    valid: bool
    credential_id: str | None
    issuer: str | None
    checks: dict[str, bool | None]
    errors: list[str] = Field(default_factory=list)
