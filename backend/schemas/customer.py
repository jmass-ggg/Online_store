from uuid import UUID
from pydantic import BaseModel, EmailStr, constr, Field, field_validator
import re
from enum import Enum


class CustomerStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class CustomerBase(BaseModel):
    username: str
    email: EmailStr = Field(..., description="Valid email")
    phone_number: str = Field(..., description="Contact phone number")

    model_config = {"from_attributes": True}


class CustomerCreate(CustomerBase):
    password: str = Field(..., min_length=6, max_length=30)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not re.search("[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search("[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v


class CustomerRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    phone_number: str
    role_name: str = "Customer"
    status: CustomerStatus

    model_config = {"from_attributes": True}


class CustomerUpdate(BaseModel):
    username: constr(min_length=5, max_length=15)
    email: EmailStr
    phone_number: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    token_type: str