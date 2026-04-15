from __future__ import annotations

from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class SellerStatus(str, Enum):
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class AccountType(str, Enum):
    BUSINESS = "BUSINESS"


class Seller(Base):
    __tablename__ = "sellers"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_sellers_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_type: Mapped[str] = mapped_column(String(50), default=AccountType.BUSINESS.value, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=SellerStatus.PENDING.value, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role_name: Mapped[str] = mapped_column(ForeignKey("roles.role_name"), default="Seller", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="seller")
    role: Mapped["Role"] = relationship("Role", back_populates="sellers")

    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="seller",
        cascade="all, delete-orphan",
    )
    delivery_charges: Mapped[list["DeliveryCharge"]] = relationship(
        "DeliveryCharge",
        back_populates="seller",
        cascade="all, delete-orphan",
    )
    personal_information: Mapped[list["SellerPersonalInformation"]] = relationship(
        "SellerPersonalInformation",
        back_populates="seller",
        cascade="all, delete-orphan",
    )
    business_addresses: Mapped[list["SellerBusinessAddress"]] = relationship(
        "SellerBusinessAddress",
        back_populates="seller",
        cascade="all, delete-orphan",
    )
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="seller")
    order_fulfillments: Mapped[list["OrderFulfillment"]] = relationship("OrderFulfillment", back_populates="seller")

    def __repr__(self) -> str:
        return f"<Seller(id={self.id}, user_id={self.user_id}, status={self.status})>"