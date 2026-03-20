from __future__ import annotations
from datetime import datetime
import uuid

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class Admin(Base):
    __tablename__ = "admin"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role_name: Mapped[str] = mapped_column(ForeignKey("roles.role_name"), default="Admin")

    roles: Mapped["Roles"] = relationship("Roles", back_populates="admin")

    def __repr__(self) -> str:
        return f"<Admin(username={self.username}, email={self.email})>"