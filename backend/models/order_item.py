from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class OrderItemStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    HAND_OVER = "HAND_OVER"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class OrderItem(Base):
    __tablename__ = "order_item"
    __table_args__ = (
        UniqueConstraint("order_id", "variant_id", name="uq_order_item_order_variant"),
        CheckConstraint("quantity > 0", name="ck_order_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_item_unit_price_nonnegative"),
        CheckConstraint("line_total >= 0", name="ck_order_item_line_total_nonnegative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variant.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(nullable=False, default=1)
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
    seller: Mapped["Seller"] = relationship("Seller", back_populates="order_items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant", back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, quantity={self.quantity})>"