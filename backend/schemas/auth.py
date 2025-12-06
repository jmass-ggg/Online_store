
from pydantic import BaseModel
from typing import Literal

class LoginRequest(BaseModel):
    email: str
    password: str
    role: Literal["customer", "seller", "admin"]
