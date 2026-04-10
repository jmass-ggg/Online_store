from typing import Optional, Tuple
from sqlalchemy.orm import Session

from backend.models.admin import Admin
from backend.models.seller import Seller
from backend.models.customer import Customer


def find_user_by_email(db: Session, email: str):
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin:
        return admin, "Admin"

    seller = db.query(Seller).filter(Seller.email == email).first()
    if seller:
        return seller, "Seller"

    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer:
        return customer, "Customer"

    return None, None


def find_user_by_username(db: Session, username: str):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin:
        return admin, "Admin"

    seller = db.query(Seller).filter(Seller.username == username).first()
    if seller:
        return seller, "Seller"

    customer = db.query(Customer).filter(Customer.username == username).first()
    if customer:
        return customer, "Customer"

    return None, None


def identity_exists(
    db: Session,
    *,
    email: Optional[str] = None,
    username: Optional[str] = None,
):
    if email:
        user, role = find_user_by_email(db, email)
        if user:
            return {
                "exists": True,
                "field": "email",
                "role": role,
                "user": user,
            }

    if username:
        user, role = find_user_by_username(db, username)
        if user:
            return {
                "exists": True,
                "field": "username",
                "role": role,
                "user": user,
            }

    return {
        "exists": False,
        "field": None,
        "role": None,
        "user": None,
    }