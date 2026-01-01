import re
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.models.product import Product

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)     
    text = re.sub(r"[\s_-]+", "-", text)         
    text = re.sub(r"^-+|-+$", "", text)          
    return text or "product"

def random_suffix(n: int = 6) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

def generate_unique_url_slug(db: Session, product_name: str, max_tries: int = 30) -> str:
    base = slugify(product_name)
    for _ in range(max_tries):
        candidate = f"{base}-{random_suffix(6)}"
        exists = db.execute(select(Product.id).where(Product.url_slug == candidate)).first()
        if not exists:
            return candidate
    raise RuntimeError("Could not generate unique url_slug")