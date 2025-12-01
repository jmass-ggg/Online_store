from pydantic import BaseModel,EmailStr

class AdminBase(BaseModel):
    username:str
    email:EmailStr
    class Config:
        orm_mdoe=True
        from_orm=True
class AdminLogin(BaseModel):
    email:EmailStr
    password:str
    class Config:
        orm_mdoe=True
        from_orm=True

class AdminRead(BaseModel):
    username:str
    email:EmailStr
    class Config:
        orm_mdoe=True
        from_orm=True