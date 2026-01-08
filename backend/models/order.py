from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Float,
    Enum as SAEnum,
    UniqueConstraint,
    Index,
    CheckConstraint,
    func,
    and_,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

class OrderStatus(str, Enum):
    PLACED = "PLACED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_buyer_id", "buyer_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_order_placed", "order_placed"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    buyer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customer.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status"),
        default=OrderStatus.PLACED,
        nullable=False,
    )

    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order_placed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["Customer"] = relationship("Customer", back_populates="orders")

    shipping_address: Mapped["OrderAddress"] = relationship(
        "OrderAddress",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    fulfillments: Mapped[list["OrderFulfillment"]] = relationship(
        "OrderFulfillment",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, buyer_id={self.buyer_id}, status={self.status})>"
