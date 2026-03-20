from __future__ import annotations
from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import String, ForeignKey, DateTime, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class ProductCategory(str, Enum):
    CLOTHES = "Clothes"
    ACCESSORIES = "Accessories"
    FOOTWEAR = "Footwear"
    JEWELRY = "Jewelry"


class TargetAudience(str, Enum):
    MEN = "Men"
    WOMEN = "Women"
    KIDS = "Kids"
    UNISEX = "Unisex"


class ProductStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    product_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    url_slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    product_category: Mapped[ProductCategory] = mapped_column(
        SAEnum(ProductCategory, name="product_category"),
        nullable=False,
    )

    target_audience: Mapped[TargetAudience] = mapped_column(
        SAEnum(TargetAudience, name="target_audience"),
        default=TargetAudience.UNISEX,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[ProductStatus] = mapped_column(
        SAEnum(ProductStatus, name="product_status"),
        default=ProductStatus.inactive,
        nullable=False,
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller: Mapped["Seller"] = relationship("Seller", back_populates="products")

    variants: Mapped[list["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductImage.sort_order",
    )

    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, product_name={self.product_name}, seller_id={self.seller_id})>"