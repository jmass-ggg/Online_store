from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class SellerBusinessAddress(Base):
    __tablename__ = "seller_business_address"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    country: Mapped[str] = mapped_column(String(100), default="NEPAL", nullable=False, index=True)
    province: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    area: Mapped[str] = mapped_column(String(255), nullable=False)

    seller: Mapped["Seller"] = relationship("Seller", back_populates="business_addresses")

    def __repr__(self) -> str:
        return f"<SellerBusinessAddress(id={self.id}, seller_id={self.seller_id})>"