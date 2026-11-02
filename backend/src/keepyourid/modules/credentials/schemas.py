
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from keepyourid.modules.credentials.enums import CredentialStatus


class CredentialCreate(BaseModel):
    credential_type: str = Field(min_length=2, max_length=255)
    subject: dict = Field(min_length=1)
    valid_until: datetime | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.valid_until is not None:
            if self.valid_until <= datetime.now(self.valid_until.tzinfo):
                raise ValueError("valid_until must be in the future.")
        return self


class CredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    credential_id: str
    organization_id: UUID
    issuer_did_id: UUID
    credential_type: str
    credential_subject: dict
    payload: dict
    proof: dict | None
    status: CredentialStatus
    valid_from: datetime
    valid_until: datetime | None
    created_at: datetime
    updated_at: datetime
    
    

class CredentialIssuanceRequest(BaseModel):
    signature: str = Field(min_length=1)
    key_id: str = Field(min_length=1, max_length=500)


class CredentialSigningRequest(BaseModel):
    signing_input: str
    key_id: str


class CredentialIssuanceResponse(BaseModel):
    credential_id: UUID
    status: CredentialStatus
    signed_credential: str

