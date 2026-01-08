# order_item.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Integer, DateTime, ForeignKey, Numeric, Enum as SAEnum,
    UniqueConstraint, Index, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class OrderItemStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "variant_id", name="uq_order_items_order_variant"),
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_seller_id", "seller_id"),
        Index("ix_order_items_variant_id", "variant_id"),
        Index("ix_order_items_order_seller", "order_id", "seller_id"),
        Index("ix_order_items_status", "item_status"),
        CheckConstraint("quantity > 0", name="ck_order_items_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_nonnegative"),
        CheckConstraint("line_total >= 0", name="ck_order_items_line_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )

    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("seller.id", ondelete="RESTRICT"), nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )

    variant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    item_status: Mapped[OrderItemStatus] = mapped_column(
        SAEnum(OrderItemStatus, name="order_item_status"),
        default=OrderItemStatus.PENDING,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    seller: Mapped["Seller"] = relationship("Seller", back_populates="orderitems")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant", back_populates="orderitems")

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, qty={self.quantity})>"
