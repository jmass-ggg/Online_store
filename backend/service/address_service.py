import requests
from sqlalchemy.orm import Session
from backend.models.address import Address
from backend.schemas.address import AddressCreate


NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


def reverse_geocode(lat: float, lng: float) -> dict:
    response = requests.get(
        NOMINATIM_URL,
        params={
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1,
        },
        headers={"User-Agent": "fastapi-address-app"},
        timeout=10,
    )

    if response.status_code != 200:
        raise Exception("Geocoding failed")

    data = response.json()
    address = data.get("address", {})

    return {
        "region": address.get("state") or address.get("region"),
        "line1": data.get("display_name"),
        "postal_code": address.get("postcode"),
        "country": address.get("country", "Nepal"),
    }


def create_address(
    db: Session,
    address: AddressCreate,
    customer_id: int,
):
    if address.latitude is None or address.longitude is None:
        raise ValueError("Latitude & longitude required")

    geo = reverse_geocode(address.latitude, address.longitude)

    data = address.model_dump()
    data.update(geo)

    db_address = Address(**data, customer_id=customer_id)

    db.add(db_address)
    db.commit()
    db.refresh(db_address)

    return db_address
