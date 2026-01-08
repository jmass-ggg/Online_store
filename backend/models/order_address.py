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


class OrderAddress(Base):
    __tablename__ = "order_addresses"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_order_addresses_order_id"),
        Index("ix_order_addresses_order_id", "order_id"),
        CheckConstraint(
            "(latitude IS NULL OR (latitude >= -90 AND latitude <= 90))",
            name="ck_order_addresses_lat_range",
        ),
        CheckConstraint(
            "(longitude IS NULL OR (longitude >= -180 AND longitude <= 180))",
            name="ck_order_addresses_lng_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)

    region: Mapped[str] = mapped_column(String(50), nullable=False)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default="Nepal", nullable=False)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    order: Mapped["Order"] = relationship("Order", back_populates="shipping_address")

    def __repr__(self) -> str:
        return f"<OrderAddress(id={self.id}, order_id={self.order_id})>"