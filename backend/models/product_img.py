from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, Boolean, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class ProductImage(Base):
    __tablename__ = "product_images"

    __table_args__ = (
        Index("ix_product_images_product_id", "product_id"),
        UniqueConstraint("product_id", "sort_order", name="uq_product_images_sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    image_url: Mapped[str] = mapped_column(String, nullable=False)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="images")

    def __repr__(self) -> str:
        return (
            f"<ProductImage(id={self.id}, product_id={self.product_id}, "
            f"is_primary={self.is_primary}, sort_order={self.sort_order})>"
        )
