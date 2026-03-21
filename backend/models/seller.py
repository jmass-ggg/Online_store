from __future__ import annotations
from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class SellerVerification(str, Enum):
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class Seller(Base):
    __tablename__ = "seller"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    business_name: Mapped[str] = mapped_column(String, nullable=False)
    business_type: Mapped[str] = mapped_column(String, default="Individual")
    business_address: Mapped[str] = mapped_column(String, nullable=False)

    kyc_document_type: Mapped[str | None] = mapped_column(String, nullable=True)
    kyc_document_number: Mapped[String | None] = mapped_column(String, nullable=True)

    bank_account_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_branch: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    status: Mapped[str] = mapped_column(String, default="REJECTED")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    role_name: Mapped[str] = mapped_column(ForeignKey("roles.role_name"), default="Seller")

    role: Mapped["Roles"] = relationship("Roles", back_populates="sellers")

    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="seller", cascade="all, delete-orphan"
    )

    orderitems: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="seller")
    orderfulfillments: Mapped[list["OrderFulfillment"]] = relationship("OrderFulfillment", back_populates="seller")
    delivery: Mapped[list["DeliveryCharge"]] = relationship("DeliveryCharge", back_populates="seller", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Seller(username={self.username}, business={self.business_name})>"