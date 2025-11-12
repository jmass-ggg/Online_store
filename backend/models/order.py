from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    order_status: Mapped[str] = mapped_column(String, default="pending")
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    order_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["Customer"] = relationship("User", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, buyer_id={self.buyer_id}, status={self.order_status}, total={self.total_price})>"
