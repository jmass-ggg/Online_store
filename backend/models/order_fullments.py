from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class FulfillmentStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    HAND_OVER = "HAND_OVER"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class OrderFulfillment(Base):
    __tablename__ = "order_fulfillment"
    __table_args__ = (
        UniqueConstraint("order_id", "seller_id", name="uq_order_fulfillment_order_seller"),
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
        ForeignKey("sellers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fulfillment_status: Mapped[FulfillmentStatus] = mapped_column(
        SAEnum(FulfillmentStatus, name="fulfillment_status"),
        default=FulfillmentStatus.PENDING,
        nullable=False,
    )
    seller_subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    packed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="fulfillments")
    seller: Mapped["Seller"] = relationship("Seller", back_populates="order_fulfillments")

    def __repr__(self) -> str:
        return f"<OrderFulfillment(id={self.id}, order_id={self.order_id}, seller_id={self.seller_id})>"