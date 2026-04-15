from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class ProductVariant(Base):
    __tablename__ = "product_variant"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_product_variant_sku"),
        UniqueConstraint("product_id", "color", "size", name="uq_product_variant_product_color_size"),
        CheckConstraint("stock_quantity >= 0", name="ck_product_variant_stock_quantity_nonnegative"),
        CheckConstraint("price > 0", name="ck_product_variant_price_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sku: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[str | None] = mapped_column(String(50), nullable=True)

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    cart_items: Mapped[list["CartItem"]] = relationship("CartItem", back_populates="variant")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="variant")

    def __repr__(self) -> str:
        return f"<ProductVariant(id={self.id}, sku={self.sku})>"