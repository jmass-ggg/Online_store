from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("product.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="reviews")
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, rating={self.rating}, user_id={self.user_id}, product_id={self.product_id})>"
