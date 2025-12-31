from __future__ import annotations
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Integer, String, ForeignKey, DateTime, Enum as SAEnum, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class ProductCategory(str, Enum):
    CLOTHES = "Clothes"
    ACCESSORIES = "Accessories"
    FOOTWEAR = "Footwear"
    JEWELRY = "Jewelry"


class ProductStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    product_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    url_slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    product_category: Mapped[ProductCategory] = mapped_column(
        SAEnum(ProductCategory, name="product_category"),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String)

    status: Mapped[ProductStatus] = mapped_column(
        SAEnum(ProductStatus, name="product_status"),
        default=ProductStatus.inactive,
        nullable=False,
    )

    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("seller.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    seller: Mapped["Seller"] = relationship("Seller", back_populates="products")

    variants: Mapped[list["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    def __repr__(self) -> str:
        return (
            f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, "
            f"qty={self.quantity}, price={self.price})>"
        )
