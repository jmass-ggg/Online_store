from __future__ import annotations
import os
import time
import threading
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

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
    {"User-Agent": USER_AGENT, "Accept": "application/json", "Accept-Language": "en"}
)

_lock = threading.Lock()
_last_call_ts = 0.0
_cache: Dict[str, Dict[str, Any]] = {}


def in_nepal_bounds(lat: float, lng: float) -> bool:
    return (
        NEPAL_BOUNDS["min_lat"] <= lat <= NEPAL_BOUNDS["max_lat"]
        and NEPAL_BOUNDS["min_lng"] <= lng <= NEPAL_BOUNDS["max_lng"]
    )


def _throttle_one_req_per_sec() -> None:
    global _last_call_ts
    with _lock:
        now = time.time()
        wait = 1.05 - (now - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.time()


def reverse_geocode(lat: float, lng: float) -> Dict[str, Any]:
    """
    Returns: region, line1, postal_code, country, country_code
    """
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
            },
            timeout=10,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Reverse geocoding failed: {type(e).__name__}")

    if resp.status_code == 403:
        raise HTTPException(
            status_code=503,
            detail="Reverse geocoding blocked by Nominatim (HTTP 403). Disable it or use another provider.",
        )
    if resp.status_code != 200:
        snip = (resp.text or "")[:120].replace("\n", " ")
        raise HTTPException(status_code=400, detail=f"Reverse geocoding failed: HTTP {resp.status_code} - {snip}")

    data = resp.json() or {}
    addr = data.get("address") or {}

    city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
    state = addr.get("state") or addr.get("province")
    road = addr.get("road") or addr.get("residential") or addr.get("path")
    suburb = addr.get("suburb") or addr.get("neighbourhood")

    line1 = ", ".join([x for x in [road, suburb, city] if x]) or (data.get("display_name") or "")

    out = {
        "region": state or "",
        "line1": line1.strip(),
        "postal_code": (addr.get("postcode") or "").strip() or None,
        "country": (addr.get("country") or "").strip() or None,
        "country_code": (addr.get("country_code") or "").lower(),
    }
    _cache[key] = out
    return out
