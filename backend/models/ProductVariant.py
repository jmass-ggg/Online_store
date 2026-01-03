from __future__ import annotations
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Integer, String, Numeric, ForeignKey,Boolean,DateTime,UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        
        UniqueConstraint("sku", name="uq_product_variants_sku"),
        UniqueConstraint("product_id", "color", "size", name="uq_variant_product_color_size"),
        CheckConstraint("stock_quantity >= 0", name="ck_variant_stock_nonnegative"),
        CheckConstraint("price > 0", name="ck_variant_price_positive"),
        Index("ix_variant_product_active", "product_id", "is_active"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    color: Mapped[str | None] = mapped_column(String)
    size: Mapped[str | None] = mapped_column(String)

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    product: Mapped["Product"] = relationship(
        "Product", back_populates="variants"
    )
