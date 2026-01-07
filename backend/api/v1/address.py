from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.address import AddressCreate, AddressResponse
from backend.service.address_service import create_address
from backend.utils.jwt import get_current_customer

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.post("/", response_model=AddressResponse)
def create_address_api(
    address: AddressCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_customer),
):
    try:
        return create_address(db, address, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
