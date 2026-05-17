from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"


class MessageResponse(BaseModel):
    message: str