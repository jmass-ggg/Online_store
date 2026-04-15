from __future__ import annotations

from sqlalchemy.orm import joinedload

from backend.database import SessionLocal


from backend.models.user import User
from backend.models.admin import AdminProfile
from backend.models.email_token_verification import EmailTokenVerification
from backend.models.refresh_token import RefreshToken
from backend.models.role import Role

from backend.utils.hashed import hashed_password


def seed_admin():
    db = SessionLocal()
    try:
        admin_exists = (
            db.query(User)
            .options(joinedload(User.admin_profile))
            .filter(
                (User.email == "admin@example.com") |
                (User.username == "admin")
            )
            .first()
        )

        if admin_exists:
            print("Admin already exists.")
            return

        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password("Admin@123"),
            is_email_verified=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        admin_profile = AdminProfile(
            user_id=admin_user.id,
            role_name="Admin",
        )

        db.add(admin_profile)
        db.commit()
        db.refresh(admin_profile)

        print("Admin seeded successfully.")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding admin: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()