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

class PaymentProvider(str,Enum):
    ESEWA = "ESEWA"

class PaymentStatus(str, Enum):
    UNPAID = "UNPAID"
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_FOUND = "NOT_FOUND"
    CANCELED = "CANCELED"
    FULL_REFUND = "FULL_REFUND"
    PARTIAL_REFUND = "PARTIAL_REFUND"

class Payment(Base):
    __tablename__="payments"
    __table_args__=(

    )
    id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    order_id:Mapped[int]=mapped_column(Integer,ForeignKey("orders.id",ondelete="CASCADE"),nullable=False)
    provider:Mapped[PaymentProvider]=mapped_column(
        SAEnum(PaymentProvider,name="payment_provider"),
        default=PaymentProvider.ESEWA,
        nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.UNPAID,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    ref_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    initiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="payments")