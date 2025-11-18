from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    buyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False
    )
    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("seller.id", ondelete="SET NULL"), nullable=True
    )

    order_status: Mapped[str] = mapped_column(String, default="pending")
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    order_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    seller: Mapped["Seller"] = relationship("Seller", back_populates="orders")

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, buyer={self.buyer_id}, status={self.order_status})>"