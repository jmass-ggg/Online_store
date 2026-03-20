from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import DateTime, ForeignKey, Numeric, Enum as SAEnum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class OrderStatus(str, Enum):
    PLACED = "PLACED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class PaymentMethod(str, Enum):
    NULL = "NULL"
    CASH_ON_DELIVERY = "CASH ON DELIVERY"
    ESEWA = "ESEWA"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_buyer_id", "buyer_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_order_placed", "order_placed"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status"),
        default=OrderStatus.PLACED,
        nullable=False,
    )

    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    payment_method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method"),
        default=PaymentMethod.NULL,
        nullable=False,
    )

    order_placed: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

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

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, buyer_id={self.buyer_id}, status={self.status})>"