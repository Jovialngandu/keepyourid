from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
	full_name: str = Field(min_length=2, max_length=255)
	email: EmailStr
	password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
	email: EmailStr
	password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: UUID
	email: str
	full_name: str
	status: str
	created_at: datetime
	updated_at: datetime


class UserSessionResponse(BaseModel):
	user: UserResponse
	access_token: str
	token_type: str = "bearer"
