from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from backend.models.order_iteam import OrderItem
from sqlalchemy import (
    Integer, DateTime, ForeignKey, Numeric, Enum as SAEnum,
    UniqueConstraint, Index, func, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from sqlalchemy.sql import and_
from backend.database import Base


class FulfillmentStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    HAND_OVER="HAND_OVER"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class OrderFulfillment(Base):
    __tablename__ = "order_fulfillments"
    __table_args__ = (
        UniqueConstraint("order_id", "seller_id", name="uq_order_fulfillments_order_seller"),
        Index("ix_order_fulfillments_order_id", "order_id"),
        Index("ix_order_fulfillments_seller_id", "seller_id"),
        Index("ix_order_fulfillments_status", "fulfillment_status"),
        Index("ix_order_fulfillments_order_seller", "order_id", "seller_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )

    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("seller.id", ondelete="CASCADE"), nullable=False
    )

    fulfillment_status: Mapped[FulfillmentStatus] = mapped_column(
        SAEnum(FulfillmentStatus, name="fulfillment_status"),
        default=FulfillmentStatus.PENDING,
        nullable=False,
    )

    seller_subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0")
    )

    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    packed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="fulfillments")
    seller: Mapped["Seller"] = relationship("Seller", back_populates="orderfulfillments")

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        primaryjoin=lambda: and_(
            foreign(OrderItem.order_id) == OrderFulfillment.order_id,
            foreign(OrderItem.seller_id) == OrderFulfillment.seller_id,
        ),
        viewonly=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<OrderFulfillment(order_id={self.order_id}, seller_id={self.seller_id}, status={self.fulfillment_status})>"