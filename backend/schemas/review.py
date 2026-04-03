from pydantic import BaseModel,Field,constr,ConfigDict
from typing import Optional
from uuid import UUID

class Review_create(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rating: int = Field(default=1, ge=1, le=5, description="Rating between 1 and 5")
    comment: constr(min_length=5, max_length=100) = Field(
        ..., description="Comment about the product"
    )

class Review_read(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rating: int = Field(default=1, ge=1, le=5, description="The rating the product")
    comment: str


class Review_update(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rating: Optional[int] = Field(None, ge=1, le=5, description="Updated rating between 1 and 5")
    comment: Optional[str] = Field(None, description="Updated review comment")
    
    