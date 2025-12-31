from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Float, ForeignKey,Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from decimal import Decimal

class OrderItem(Base):
    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[Decimal] = mapped_column(Numeric(10,2))

    order: Mapped["Order"] = relationship("Order", back_populates="items")

    product: Mapped["Product"] = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, quantity={self.quantity}, price={self.price})>"

