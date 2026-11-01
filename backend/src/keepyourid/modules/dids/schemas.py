
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
