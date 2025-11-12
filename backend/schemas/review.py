from pydantic import BaseModel,Field,constr
from typing import Optional

class Review_create(BaseModel):
    rating: int = Field(default=1, ge=1, le=5, description="Rating between 1 and 5")
    comment : constr(min_length=5,max_length=100)=Field(...,description="Comment about the product")
    
    class Config:
        orm_mode=True
        from_attributes=True
        
class Review_read(BaseModel):
    id : int
    rating : int = Field(default=1,ge=1,le=5,description="The rating the product")
    comment : str
    
    class Config:
        orm_mode=True
        from_attributes=True
        
class Review_update(BaseModel):
    rating : Optional[int] = Field(None, ge=1, le=5, description="Updated rating between 1 and 5")
    comment : Optional[str] = Field(None, description="Updated review comment")
    
    class Config:
        orm_mode = True
        from_attributes = True
    
    