from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    product_category: Mapped[str] = mapped_column(String, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, index=True)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="product", cascade="all, delete-orphan"
    )
    user: Mapped["Customer"] = relationship("User", back_populates="products")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.product_name}, category={self.product_category}, seller_id={self.seller_id})>"
