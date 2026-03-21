from __future__ import annotations

import backend.models  # important: register all models first

from backend.database import SessionLocal
from backend.core import error_handler
from backend.models.admin import Admin
from backend.utils.hashed import hashed_password

db = SessionLocal()

def seed_admin():
    try:
        admin_exists = db.query(Admin).filter(
            (Admin.email == "admin@example.com") |
            (Admin.username == "admin")
        ).first()

        if admin_exists:
            raise error_handler(400, "Admin already exists")

        admin = Admin(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password("Admin@123"),
            role_name="Admin",
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Admin seeded successfully.")
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding admin: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()