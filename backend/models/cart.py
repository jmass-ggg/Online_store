from __future__ import annotations
from backend.database import Base
from sqlalchemy import Integer,String,Float,ForeignKey,Column,DateTime, func,Numeric
from datetime import datetime
from sqlalchemy.orm import relationship,Mapped,mapped_column
from enum import Enum
from decimal import Decimal
from sqlalchemy.dialects.postgresql import UUID
import uuid

class CartStauts(str,Enum):
    ACTIVE = "ACTIVE"
    CHECKED_OUT = "CHECKED_OUT"
    ABANDONED = "ABANDONED"

class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[uuid.uuid4] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    buyer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customer.id", ondelete="CASCADE"), nullable=False
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