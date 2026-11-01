from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from keepyourid.modules.organizations.enums import OrganizationStatus


class OrganizationCreate(BaseModel):
    legal_name: str = Field(min_length=2, max_length=255)
    registration_number: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str
    registration_number: str
    email: str
    phone: str | None
    did: str | None
    status: OrganizationStatus
    created_at: datetime
    updated_at: datetime