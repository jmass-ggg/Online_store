from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRegisterResponse(BaseModel):
    message: str
    user_id: UUID
    username: str
    email: EmailStr
    account_status: str
    is_email_verified: bool

    model_config = ConfigDict(from_attributes=True)