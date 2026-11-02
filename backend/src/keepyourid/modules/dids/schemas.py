from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DIDCreate(BaseModel):
    identifier: str = Field(min_length=5, max_length=500)
    method: str = Field(min_length=1, max_length=50)
    document: dict


class DIDResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    identifier: str
    method: str
    document: dict
    created_at: datetime
    updated_at: datetime


class DIDChallengeCreate(BaseModel):
    purpose: str = Field(min_length=1, max_length=100)
    domain: str = Field(min_length=1, max_length=255)


class DIDChallengeResponse(BaseModel):
    challenge_id: UUID
    challenge: str
    purpose: str
    domain: str
    issued_at: datetime
    expires_at: datetime
    message: str


class DIDProofSubmission(BaseModel):
    challenge_id: UUID
    verification_method: str = Field(min_length=1, max_length=500)
    signature: str = Field(pattern=r"^0x[0-9a-fA-F]+$")


class DIDVerificationResponse(BaseModel):
    did_id: UUID
    identifier: str
    status: str
    verification_method: str
    signer_address: str
    verified_at: datetime
