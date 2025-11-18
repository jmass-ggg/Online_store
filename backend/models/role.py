from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.database import Base


class Roles(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    descripted: Mapped[str | None] = mapped_column(String, nullable=True)

    users: Mapped[list["Customer"]] = relationship("Customer", back_populates="role")
    admins: Mapped[list["Admin"]] = relationship("Admin", back_populates="roles")
    def __repr__(self):
        return f"<Role(id={self.id}, role_name={self.role_name})>"