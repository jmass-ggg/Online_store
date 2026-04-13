from __future__ import annotations

from decimal import Decimal
import uuid

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class DeliveryCharge(Base):
    __tablename__ = "delivery_charge"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_charge: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0, nullable=False)

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    seller: Mapped["Seller"] = relationship("Seller", back_populates="delivery_charges")

    def __repr__(self) -> str:
        return f"<DeliveryCharge(id={self.id}, seller_id={self.seller_id})>"