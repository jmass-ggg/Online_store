from __future__ import annotations
from backend.database import Base
from sqlalchemy import Integer,String,Float,ForeignKey,Column,DateTime, func
from datetime import datetime
from sqlalchemy.orm import relationship,Mapped,mapped_column

class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False,primary_key=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False,primary_key=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    status: Mapped[str] = mapped_column(String, default="active")

    role_name: Mapped[str] = mapped_column(
        ForeignKey("roles.role_name"), default="Customer"
    )

    role: Mapped["Roles"] = relationship("Roles", back_populates="users")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="user")
    carts: Mapped[list["Cart"]] = relationship("Cart", back_populates="buyer")
    addresses: Mapped[list["Address"]] = relationship(
    "Address", back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Customer(username={self.username}, email={self.email})>"



