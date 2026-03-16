from __future__ import annotations
from backend.database import Base

from sqlalchemy.orm import relationship,Mapped,mapped_column

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Float,
    Enum as SAEnum,
    UniqueConstraint,
    Index,
    CheckConstraint,
    func,
    and_,
    text,
)
from decimal import Decimal
class DeliveryCharge(Base):
    __tablename__="deliveryCharge"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    Delivery:Mapped[Decimal]=mapped_column(Numeric(5,2),default=0.00)
    seller_id:Mapped[int]=mapped_column(Integer,
                                        ForeignKey("seller.id",
                                                   ondelete="CASCADE"),nullable=False
                                        )
    seller:Mapped["Seller"]=relationship("Seller",back_populates="delivery")
    