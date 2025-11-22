from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.database import Base

class Seller(Base):
    __tablename__ = "seller"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Authentication
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # Business Info
    business_name: Mapped[str] = mapped_column(String, nullable=False)
    business_type: Mapped[str] = mapped_column(String, default="Individual")
    business_address: Mapped[str] = mapped_column(String, nullable=False)

    # KYC
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    kyc_document_type: Mapped[str | None] = mapped_column(String, nullable=True)
    kyc_document_number: Mapped[str | None] = mapped_column(String, nullable=True)
    kyc_document_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Banking
    bank_account_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_branch: Mapped[str | None] = mapped_column(String, nullable=True)

    # Stats
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    total_sales: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    status: Mapped[str] = mapped_column(String, default="REJECTED")
    # Relationships
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role_name: Mapped[str] = mapped_column(
        ForeignKey("roles.role_name"),
        default="Seller"
    )

    # relationship to Roles
    role = relationship("Roles", back_populates="sellers")
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="seller", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="seller")

    def __repr__(self):
        return f"<Seller(username={self.username}, business={self.business_name})>"