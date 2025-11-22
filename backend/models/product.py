from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    product_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    product_category: Mapped[str] = mapped_column(String, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("seller.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    order_items = relationship("OrderItem", back_populates="product")
    seller: Mapped["Seller"] = relationship("Seller", back_populates="products")
    reviews = relationship("Review", back_populates="product")
    def __repr__(self):
        return f"<Product(name={self.product_name}, price={self.price})>"