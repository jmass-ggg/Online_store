from __future__ import annotations

import os
import time
import threading
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.address import Address
from backend.schemas.address import AddressCreate

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

REVERSE_GEOCODE_ENABLED = os.getenv("REVERSE_GEOCODE_ENABLED", "false").lower() == "true"


NOMINATIM_EMAIL = os.getenv("NOMINATIM_EMAIL", "")
USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT",
    f"online-store/1.0 (contact: {NOMINATIM_EMAIL or 'no-email-set'})",
)

NEPAL_BOUNDS = {"min_lat": 26.3, "max_lat": 30.5, "min_lng": 80.0, "max_lng": 88.3}

_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en",
    }
)

_lock = threading.Lock()
_last_call_ts = 0.0

_cache: Dict[str, Dict[str, Any]] = {}


def _throttle_one_req_per_sec() -> None:
    global _last_call_ts
    with _lock:
        now = time.time()
        wait = 1.05 - (now - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.time()


def reverse_geocode(lat: float, lng: float) -> Dict[str, Any]:
    key = f"{lat:.6f},{lng:.6f}"
    if key in _cache:
        return _cache[key]

    _throttle_one_req_per_sec()

    try:
        resp = _session.get(
            NOMINATIM_URL,
            params={
                "lat": lat,
                "lon": lng,
                "format": "jsonv2",
                "addressdetails": 1,
                "zoom": 18,
                
                "email": NOMINATIM_EMAIL or None,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Reverse geocoding request failed: {type(e).__name__}")

    if resp.status_code == 403:
        raise HTTPException(
            status_code=503,
            detail="Reverse geocoding unavailable (blocked by Nominatim). Disable reverse geocoding or use another provider.",
        )

    if resp.status_code != 200:
        body_snip = (resp.text or "")[:120].replace("\n", " ")
        raise HTTPException(status_code=400, detail=f"Reverse geocoding failed: HTTP {resp.status_code} - {body_snip}")

    data = resp.json() or {}
    addr = data.get("address", {}) or {}

    city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
    state = addr.get("state") or addr.get("province")
    road = addr.get("road") or addr.get("residential") or addr.get("path")
    suburb = addr.get("suburb") or addr.get("neighbourhood")
    line1 = ", ".join([x for x in [road, suburb, city] if x])

    out = {
        "region": state,
        "line1": line1,
        "postal_code": addr.get("postcode"),
        "country": addr.get("country"),
        "country_code": (addr.get("country_code") or "").lower(),
    }
    _cache[key] = out
    return out

def _to_dict(model):
    if hasattr(model, "model_dump"): 
        return model.model_dump()
    return model.dict()  

def create_address(db: Session, address_in: AddressCreate, customer_id: int) -> Address:

    if address_in.latitude is None or address_in.longitude is None:
        raise HTTPException(status_code=400, detail="Latitude and longitude are required")

    lat = float(address_in.latitude)
    lng = float(address_in.longitude)

    if not (-90.0 <= lat <= 90.0):
        raise HTTPException(status_code=400, detail="Invalid latitude")
    if not (-180.0 <= lng <= 180.0):
        raise HTTPException(status_code=400, detail="Invalid longitude")

    in_nepal_bounds = (
        NEPAL_BOUNDS["min_lat"] <= lat <= NEPAL_BOUNDS["max_lat"]
        and NEPAL_BOUNDS["min_lng"] <= lng <= NEPAL_BOUNDS["max_lng"]
    )
    if not in_nepal_bounds:
        raise HTTPException(status_code=400, detail="Service available only in Nepal")

    data = _to_dict(address_in)

    geo: Optional[Dict[str, Any]] = None
    if REVERSE_GEOCODE_ENABLED:
        geo = reverse_geocode(lat, lng)

        if geo.get("country_code") and geo.get("country_code") != "np":
            raise HTTPException(status_code=400, detail="Service available only in Nepal")

        data["region"] = (geo.get("region") or data.get("region") or "").strip()
        data["line1"] = (geo.get("line1") or data.get("line1") or "").strip()
        data["postal_code"] = geo.get("postal_code") or data.get("postal_code")
        data["country"] = (geo.get("country") or data.get("country") or "Nepal").strip()
    else:

        data["region"] = (data.get("region") or "").strip()
        data["line1"] = (data.get("line1") or "").strip()
        data["country"] = (data.get("country") or "Nepal").strip()


    if not data["region"]:
        raise HTTPException(status_code=400, detail="Region is required")
    if not data["line1"]:
        raise HTTPException(status_code=400, detail="Address line1 is required")

    db_address = Address(**data, customer_id=customer_id)
    try:
        db.add(db_address)
        db.commit()
        db.refresh(db_address)
        return db_address
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Address save failed (invalid data)")
