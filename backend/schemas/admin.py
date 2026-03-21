from pydantic import BaseModel,EmailStr,ConfigDict

class AdminBase(BaseModel):
    username:str
    email:EmailStr
    model_config = ConfigDict(from_attributes=True)
class AdminLogin(BaseModel):
    email:EmailStr
    password:str
    model_config = ConfigDict(from_attributes=True)

class AdminRead(BaseModel):
    username:str
    email:EmailStr
    model_config = ConfigDict(from_attributes=True)
        
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
    model_config = ConfigDict(from_attributes=True)