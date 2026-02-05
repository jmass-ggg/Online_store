from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.address import AddressCreate, AddressResponse
from backend.service.address_service import create_address
from backend.utils.jwt import get_current_customer
from backend.models.customer import Customer

router = APIRouter(prefix="/addresses", tags=["Addresses"])

@router.post("/", response_model=AddressResponse)
def create_address_api(
    address: AddressCreate,
    db: Session = Depends(get_db),
    user: Customer = Depends(get_current_customer),
):
    db_address = create_address(db, address, user.id)
    return db_address
