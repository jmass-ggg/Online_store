from pydantic import BaseModel,Field
from typing import Optional
from datetime import datetime

class AddressCreate(BaseModel):
    full_name: str=Field(max_length=100)
    phone_number: str = Field(..., max_length=20)
    region: str
    line1: str
    line2: Optional[str] = None
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str =Field ("Nepal",max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default_shipping: bool = False
    is_default_billing: bool = False

class AddressUpdate(BaseModel):
    
    full_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)

    region: Optional[str] = Field(None, max_length=50)
    line1: Optional[str] = Field(None, max_length=255)
    line2: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=50)

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    is_default_shipping: Optional[bool] = None
    is_default_billing: Optional[bool] = None
    
class AddressResponse(AddressCreate):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_omr=True
        omr_mode=True
