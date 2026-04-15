from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
from backend.database import Base

class CustomerStatus(str, Enum):
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    
class CustomerProfile(Base):
    __tablename__ = "customer_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_customer_profiles_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50),  default=CustomerStatus.PENDING.value, nullable=False, index=True)
    role_name: Mapped[str] = mapped_column(ForeignKey("roles.role_name"), default="Customer", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="customer_profile")
    role: Mapped["Role"] = relationship("Role", back_populates="customer_profiles")

    addresses: Mapped[list["AddressCustomer"]] = relationship(
        "AddressCustomer",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    carts: Mapped[list["Cart"]] = relationship(
        "Cart",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CustomerProfile(id={self.id}, user_id={self.user_id})>"