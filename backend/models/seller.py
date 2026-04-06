from __future__ import annotations
from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class SellerVerification(str, Enum):
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"


class AccountType(str, Enum):
    BUSINESS = "BUSINESS"


class Seller(Base):
    __tablename__ = "seller"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    username: Mapped[str] = mapped_column(String, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    account_type: Mapped[str] = mapped_column(String, default=AccountType.BUSINESS.value)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    status: Mapped[str] = mapped_column(String, default=SellerVerification.PENDING.value, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    role_name: Mapped[str] = mapped_column(ForeignKey("roles.role_name"), default="Seller", index=True)

  
    role: Mapped["Roles"] = relationship("Roles", back_populates="sellers")
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="seller", cascade="all, delete-orphan"
    )
    orderitems: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="seller")
    orderfulfillments: Mapped[list["OrderFulfillment"]] = relationship("OrderFulfillment", back_populates="seller")
    delivery: Mapped[list["DeliveryCharge"]] = relationship(
        "DeliveryCharge", back_populates="seller", cascade="all, delete-orphan"
    )
    seller_verification_emails: Mapped[list["SellerEmailTokenVerification"]] = relationship(
        "SellerEmailTokenVerification", back_populates="seller", cascade="all, delete-orphan"
    )
    seller_information: Mapped[list["SellerInformation"]] = relationship(
        "SellerInformation", back_populates="seller", cascade="all, delete-orphan"
    )
    seller_business_address: Mapped[list["SellerBusinessAddress"]] = relationship(
        "SellerBusinessAddress", back_populates="seller", cascade="all, delete-orphan"
    )
    def __repr__(self):
        return f"<Seller(username={self.username}, email={self.email})>"


class SellerEmailTokenVerification(Base):
    __tablename__ = "selleremailverification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seller.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    expired_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    seller: Mapped["Seller"] = relationship(
        "Seller", back_populates="seller_verification_emails"
    )


class SellerInformation(Base):
    __tablename__ = "seller_information" 

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seller.id", ondelete="CASCADE"), nullable=False, index=True
    )

    legal_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pan_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    business_document_photo: Mapped[str] = mapped_column(String, nullable=False)
    account_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    account_number: Mapped[str] = mapped_column(String, nullable=False, index=True)
    bank_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    branch_name: Mapped[str] = mapped_column(String, nullable=False)
    cheque_photo: Mapped[str] = mapped_column(String, nullable=False)

    seller: Mapped["Seller"] = relationship(
        "Seller", back_populates="seller_information"
    )

class SellerBusinessAddress(Base):
    __tablename__ = "seller_business_address" 

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seller.id", ondelete="CASCADE"), nullable=False, index=True
    )
    country: Mapped[str] = mapped_column(String, default="NEPAL",nullable=False, index=True)
    province: Mapped[str] = mapped_column(String, nullable=False, index=True)
    district: Mapped[str] = mapped_column(String, nullable=False, index=True)
    area: Mapped[str] = mapped_column(String, nullable=False)

    seller: Mapped["Seller"] = relationship(
        "Seller", back_populates="seller_business_address"
    )