from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from keepyourid.modules.dids.enums import DIDStatus


class HolderDIDCreate(BaseModel):
    identifier: str = Field(min_length=1, max_length=500)
    method: str = Field(default="ethr", min_length=2, max_length=50)
    document: dict = Field(default_factory=dict)


class HolderDIDResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    identifier: str
    method: str
    document: dict
    status: DIDStatus
    created_at: datetime
    updated_at: datetime


class HolderDIDChallengeCreate(BaseModel):
    purpose: str = Field(min_length=1, max_length=100)
    domain: str = Field(min_length=1, max_length=255)


class HolderDIDChallengeResponse(BaseModel):
    challenge_id: UUID
    challenge: str
    purpose: str
    domain: str
    issued_at: datetime
    expires_at: datetime
    message: str


class HolderDIDProofSubmission(BaseModel):
    challenge_id: UUID
    signature: str = Field(min_length=1, max_length=4000)
    verification_method: str = Field(min_length=1, max_length=500)
    purpose: str = Field(default="did_authentication", min_length=1, max_length=100)
    domain: str = Field(default="keepyourid.local", min_length=1, max_length=255)


class HolderDIDVerificationResponse(BaseModel):
    did_id: UUID
    identifier: str
    status: str
    verification_method: str
    signer_address: str
    holder_user_id: str
    verified_at: datetime
