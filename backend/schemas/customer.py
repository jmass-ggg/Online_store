from pydantic import BaseModel, EmailStr, constr,validator,Field
import re
from datetime import datetime
from enum import Enum

class CustomerStatus(str,Enum):
    active="active"
    inactive="inactive"
    suspended="suspended"

class CustomerBase(BaseModel):
    username:str 
    email: EmailStr=Field(...,description="Valid emial address of the user")
    phone_number:str=Field(...,description="")
    address:str=Field(...,description="The address of the user")
    payment:str=Field(default="Cash on delivery",description="The payment method of the user")
    role_name:str=Field(default="Customer",description="The role of the user")
    class Config:
        orm_mode = True
        from_attributes = True

    
class CustomerCreate(CustomerBase):
    password: str=Field(...,min_length=6,max_length=30,description="Valid and Strong password")
    status:str=Field(default=CustomerStatus.active,description="The status of the user")
    @validator('password')
    def strong_password(cls,v):
        if not re.search("[A-Z]",v):
            raise ValueError("The password should contain Uppercase")
        if not re.search("[a-z]",v):
            raise ValueError("The password should contain lowercase")
        return v
    

class CustomerRead(CustomerBase):
    id:int=Field(...,description="The unique Id of user")
    
    class Config:
        orm_mode = True
        from_attributes = True
        

class CustomerUpdate(BaseModel):   
    username : constr(min_length=5,max_length=15)=Field(...,description="Update username")
    email : EmailStr=Field(...,description="Update email")
    phone_number:str=Field(...,description="")
    class Config:
        orm_mode = True
        from_attributes = True
    
class TokenResponse(BaseModel):
    access_token: str=Field(...,description="JWT access token")
    token_type: str=Field(...,description="The token type")
    