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
            "zoom": 18,
        },
        headers={"User-Agent": "fastapi-address-app"},
        timeout=5,
    )

    if response.status_code != 200:
        raise ValueError("Reverse geocoding failed")

    data = response.json()
    address = data.get("address", {})

    return {
        "region": address.get("state"),
        "line1": ", ".join(
            filter(
                None,
                [
                    address.get("road"),
                    address.get("suburb"),
                    address.get("city"),
                ],
            )
        ),
        "postal_code": address.get("postcode"),
        "country": address.get("country"),
    }

def create_address(
    db: Session,
    address: AddressCreate,
    customer_id: int,
):
    if address.latitude is None or address.longitude is None:
        raise ValueError("Latitude and longitude are required")

    if not (-90 <= address.latitude <= 90):
        raise ValueError("Invalid latitude")

    if not (-180 <= address.longitude <= 180):
        raise ValueError("Invalid longitude")

    geo = reverse_geocode(address.latitude, address.longitude)

    if geo.get("country") != "Nepal":
        raise ValueError("Service available only in Nepal")

    data = address.model_dump()

    data["region"] = geo.get("region") or data.get("region")
    data["line1"] = geo.get("line1") or data.get("line1")
    data["postal_code"] = geo.get("postal_code")
    data["country"] = geo.get("country", "Nepal")

    db_address = Address(
        **data,
        customer_id=customer_id,
    )

    db.add(db_address)
    db.commit()
    db.refresh(db_address)

    return db_address
