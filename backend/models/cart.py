from __future__ import annotations
from backend.database import Base
from sqlalchemy import Integer,String,Float,ForeignKey,Column,DateTime, func
from datetime import datetime
from sqlalchemy.orm import relationship,Mapped,mapped_column
from enum import Enum

class CartStauts(str,Enum):
    ACTIVE = "ACTIVE"
    CHECKED_OUT = "CHECKED_OUT"
    ABANDONED = "ABANDONED"

class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    buyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, default="ACTIVE", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    buyer: Mapped["Customer"] = relationship("Customer", back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(
    "CartItem", back_populates="cart", cascade="all, delete-orphan"
)

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, buyer_id={self.buyer_id}, status={self.status})>"