import re
from uuid import uuid4
from sqlalchemy.orm import Session

from backend.models.ProductVariant import ProductVariant


def _clean_part(text: str) -> str:
    """
    Uppercase + replace non-alphanumerics with '-' (SKU-safe).
    """
    text = text.strip().upper()
    text = re.sub(r"[^A-Z0-9]+", "-", text)
    return text.strip("-")


def generate_hybrid_sku(
    db: Session,
    product_slug: str,
    color: str | None = None,
    size: str | None = None,
    suffix_len: int = 4,
    max_tries: int = 10,
) -> str:
    """
    Hybrid SKU = HUMAN-PARTS + RANDOM-SUFFIX
    Example: "NIKE-AIR-MAX-RED-M-7F3A"

    - Ensures uniqueness by checking ProductVariant.sku in DB.
    - Regenerates suffix if collision occurs.
    """
    base_parts = [_clean_part(product_slug)]
    if color:
        base_parts.append(_clean_part(color))
    if size:
        base_parts.append(_clean_part(size))

    base = "-".join([p for p in base_parts if p])

    for _ in range(max_tries):
        suffix = uuid4().hex[:suffix_len].upper()
        sku = f"{base}-{suffix}"

        exists = db.query(ProductVariant.id).filter(ProductVariant.sku == sku).first()
        if not exists:
            return sku

    raise RuntimeError("Could not generate unique SKU after multiple attempts")
