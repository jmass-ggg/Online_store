from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripted: Mapped[str | None] = mapped_column(String(255), nullable=True)

    admin_profiles: Mapped[list["AdminProfile"]] = relationship("AdminProfile", back_populates="role")
    customer_profiles: Mapped[list["CustomerProfile"]] = relationship("CustomerProfile", back_populates="role")
    sellers: Mapped[list["Seller"]] = relationship("Seller", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, role_name={self.role_name})>"