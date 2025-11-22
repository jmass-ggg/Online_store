from pydantic import BaseModel, EmailStr, constr, Field, validator
import re
from enum import Enum

# -------------------------
# ENUM
# -------------------------
class CustomerStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


# -------------------------
# BASE MODEL (only user input fields)
# -------------------------
class CustomerBase(BaseModel):
    username: str
    email: EmailStr=Field(..., description="Valid email address")
    phone_number: str=Field(..., description="Contact phone number")
    address: str=Field(..., description="Residential address")
    

    class Config:
        orm_mode = True
        from_attributes = True


# -------------------------
# CREATE MODEL (used for registration)
# Note: role_name REMOVED (only server sets it)
# -------------------------
class CustomerCreate(CustomerBase):
    password: str = Field(..., min_length=6, max_length=30)

    @validator('password')
    def strong_password(cls, v):
        if not re.search("[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search("[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v


# -------------------------
# READ MODEL (response sent to client)
# role_name is shown, but cannot be changed
# -------------------------
class CustomerRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: str
    address: str
    role_name: str = "Customer"
    status: CustomerStatus

    class Config:
        orm_mode = True
        from_attributes = True


# -------------------------
# UPDATE MODEL (user can update limited fields)
# NO role_name, NO password
# -------------------------
class CustomerUpdate(BaseModel):
    username: constr(min_length=5, max_length=15)
    email: EmailStr
    phone_number: str

    class Config:
        orm_mode = True
        from_attributes = True


# -------------------------
# TOKEN RESPONSE MODEL
# -------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
