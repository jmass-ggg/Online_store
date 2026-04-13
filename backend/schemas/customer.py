from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field



class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:UUID
    username:str
    email:str
    is_email_verified: bool
    
class CustomerRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class CustomerProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    
    role_name: str
    user:UserPublic

    model_config = ConfigDict(from_attributes=True)



class CustomerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=100)
    email: EmailStr

