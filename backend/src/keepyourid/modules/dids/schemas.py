from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from keepyourid.modules.dids.enums import DIDStatus
from typing import Any


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
    status: DIDStatus
    created_at: datetime
    updated_at: datetime


class DIDListResponse(BaseModel):
    items: list[DIDResponse]


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


class DIDBlockchainRegistrationResponse(BaseModel):
    transaction_id: str | None = None
    transaction_hash: str | None = None
    block_number: int | None = None
    gas_used: int | None = None
    status: str
    error: str | None = None



      
class DIDVerificationResponse(BaseModel):
    did_id: UUID
    identifier: str
    status: str
    verification_method: str
    signer_address: str
    verified_at: datetime
    blockchain_registration: DIDBlockchainRegistrationResponse | None = None
    
class DIDBlockchainIssuerResponse(BaseModel):
    did_hash: str
    metadata_hash: str
    status: str
    registered_at: int
    updated_at: int


class DIDBlockchainStatusResponse(BaseModel):
    did_id: UUID
    identifier: str
    registered: bool
    active: bool
    issuer: DIDBlockchainIssuerResponse | None = None