from __future__ import annotations
from decimal import Decimal
from sqlalchemy import Integer, ForeignKey, UniqueConstraint,Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    cart_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    variant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price:Mapped[Decimal]=mapped_column(Numeric(12,2),nullable=False)
    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant", back_populates="cart_items")
