from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customer.id", ondelete="CASCADE"), nullable=False
    )

    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    user: Mapped["Customer"] = relationship("Customer", back_populates="reviews")

    def __repr__(self) -> str:
        return (
            f"<Review(id={self.id}, rating={self.rating}, "
            f"product_id={self.product_id}, user_id={self.user_id})>"
        )

