from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class SellerPersonalInformation(Base):
    __tablename__ = "seller_personal_information"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    legal_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    pan_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    business_document_photo: Mapped[str] = mapped_column(String(500), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    account_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cheque_photo: Mapped[str] = mapped_column(String(500), nullable=False)

    seller: Mapped["Seller"] = relationship("Seller", back_populates="personal_information")

    def __repr__(self) -> str:
        return f"<SellerPersonalInformation(id={self.id}, seller_id={self.seller_id})>"