from __future__ import annotations
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import update, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.address import Address
from backend.schemas.address import AddressCreate, AddressUpdate
from backend.service.geocoding import (
    REVERSE_GEOCODE_ENABLED,
    in_nepal_bounds,
    reverse_geocode,
)
from uuid import UUID

def _dump(pydantic_obj) -> Dict[str, Any]:
    
    if hasattr(pydantic_obj, "model_dump"):
        return pydantic_obj.model_dump(exclude_unset=True)
    return pydantic_obj.dict(exclude_unset=True)

def _check_max_len(value:Optional[str],max_len:int,field:str):
    if value is not None and len(value) > max_len:
        raise HTTPException(
            status_code=400,
            detail=f"{field} must be at most {max_len} characters",
        )

def _validate_latlng(lat: float, lng: float) -> None:
    if not (-90.0 <= lat <= 90.0):

        raise HTTPException(status_code=400, detail="Invalid latitude")
    if not (-180.0 <= lng <= 180.0):
        raise HTTPException(status_code=400, detail="Invalid longitude")
    if not in_nepal_bounds(lat, lng):
        raise HTTPException(status_code=400, detail="Service available only in Nepal")

def _validate_address_lengths(data: Dict[str, Any]) -> None:
    _check_max_len(data.get("full_name"), 100, "full_name")
    _check_max_len(data.get("phone_number"), 20, "phone_number")
    _check_max_len(data.get("region"), 50, "region")
    _check_max_len(data.get("line1"), 255, "line1")
    _check_max_len(data.get("line2"), 255, "line2")
    _check_max_len(data.get("postal_code"), 20, "postal_code")
    _check_max_len(data.get("country"), 50, "country")


def _normalize_str(x: Optional[str]) -> Optional[str]:
    if x is None:
        return None
    x = x.strip()
    return x or None


def create_address(db: Session, address_in: AddressCreate, customer_id: UUID) -> Address:
    data = _dump(address_in)

    lat = float(data["latitude"])
    lng = float(data["longitude"])
    _validate_latlng(lat, lng)

    
    if REVERSE_GEOCODE_ENABLED:
        geo = reverse_geocode(lat, lng)
        if geo.get("country_code") and geo["country_code"] != "np":
            raise HTTPException(status_code=400, detail="Service available only in Nepal")

        data["region"] = geo.get("region") or data.get("region")
        data["line1"] = geo.get("line1") or data.get("line1")
        data["postal_code"] = geo.get("postal_code") or data.get("postal_code")
        data["country"] = geo.get("country") or data.get("country") or "Nepal"

 
    data["region"] = _normalize_str(data.get("region")) or ""
    data["line1"] = _normalize_str(data.get("line1")) or ""
    data["line2"] = _normalize_str(data.get("line2"))
    data["postal_code"] = _normalize_str(data.get("postal_code"))
    data["country"] = _normalize_str(data.get("country")) or "Nepal"
    _validate_address_lengths(data)
    if not data["region"]:
        raise HTTPException(status_code=400, detail="Region is required")
    if not data["line1"]:
        raise HTTPException(status_code=400, detail="Address line1 is required")

    try:
      
        if data.get("is_default_shipping"):
            db.execute(
                update(Address)
                .where(Address.customer_id == customer_id)
                .values(is_default_shipping=False)
            )
        if data.get("is_default_billing"):
            db.execute(
                update(Address)
                .where(Address.customer_id == customer_id)
                .values(is_default_billing=False)
            )
        existing = (
        db.query(Address)
        .filter(
            Address.customer_id == customer_id,
            Address.line1 == data["line1"],
            Address.latitude == lat,
            Address.longitude == lng,
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="Address already exists")

        db_address = Address(customer_id=customer_id, **data)
        
        db.add(db_address)

        db.commit()
        db.refresh(db_address)
        return db_address

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Address save failed (invalid data)")


def list_addresses(db: Session, customer_id: UUID) -> list[Address]:
    stmt = select(Address).where(Address.customer_id == customer_id).order_by(Address.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def delete_address(db: Session, customer_id: UUID, address_id: UUID) -> None:
    addr = db.get(Address, address_id)
    if not addr or addr.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Address not found")

    with db.begin():
        db.delete(addr)


def update_address(db: Session, customer_id: UUID, address_id: UUID, patch: AddressUpdate) -> Address:
    addr = db.get(Address, address_id)
    if not addr or addr.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Address not found")

    data = _dump(patch)

    
    if "latitude" in data or "longitude" in data:
        lat = float(data.get("latitude", addr.latitude))
        lng = float(data.get("longitude", addr.longitude))
        if lat is None or lng is None:
            raise HTTPException(status_code=400, detail="Both latitude and longitude are required")
        _validate_latlng(lat, lng)

        if REVERSE_GEOCODE_ENABLED:
            geo = reverse_geocode(lat, lng)
            if geo.get("country_code") and geo["country_code"] != "np":
                raise HTTPException(status_code=400, detail="Service available only in Nepal")
            data["region"] = geo.get("region") or data.get("region")
            data["line1"] = geo.get("line1") or data.get("line1")
            data["postal_code"] = geo.get("postal_code") or data.get("postal_code")
            data["country"] = geo.get("country") or data.get("country") or "Nepal"


    for k in ["region", "line1", "line2", "postal_code", "country", "full_name", "phone_number"]:
        if k in data:
            data[k] = _normalize_str(data[k])


    try:
        with db.begin():
            if data.get("is_default_shipping") is True:
                db.execute(
                    update(Address)
                    .where(Address.customer_id == customer_id)
                    .values(is_default_shipping=False)
                )
            if data.get("is_default_billing") is True:
                db.execute(
                    update(Address)
                    .where(Address.customer_id == customer_id)
                    .values(is_default_billing=False)
                )

            for k, v in data.items():
                setattr(addr, k, v)

        db.refresh(addr)
        return addr
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Address update failed")
