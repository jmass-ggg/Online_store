from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AddressCreate(BaseModel):
    full_name: str
    phone_number: str
    region: str
    line1: str
    line2: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Nepal"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default_shipping: bool = False
    is_default_billing: bool = False


class AddressResponse(AddressCreate):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_omr=True
        omr_mode=True
