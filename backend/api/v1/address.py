from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.customer import Customer
from backend.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from backend.service.address_service import (
    create_address,
    list_addresses,
    delete_address,
    update_address,
)
from backend.utils.jwt import get_current_customer

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address_api(
    address: AddressCreate,
    db: Session = Depends(get_db),
    user: Customer = Depends(get_current_customer),
):
    return create_address(db, address, user.id)


@router.get("/", response_model=list[AddressResponse])
def list_my_addresses(
    db: Session = Depends(get_db),
    user: Customer = Depends(get_current_customer),
):
    return list_addresses(db, user.id)

@router.patch("/{address_id}", response_model=AddressResponse)
def patch_address(
    address_id: int,
    patch: AddressUpdate,
    db: Session = Depends(get_db),
    user: Customer = Depends(get_current_customer),
):
    return update_address(db, user.id, address_id, patch)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_address(
    address_id: int,
    db: Session = Depends(get_db),
    user: Customer = Depends(get_current_customer),
):
    delete_address(db, user.id, address_id)
    return None
