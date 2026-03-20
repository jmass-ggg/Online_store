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
from sqlalchemy.dialects.postgresql import UUID
import uuid

class DeliveryCharge(Base):
    __tablename__="deliveryCharge"
    
    id: Mapped[uuid.uuid4] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    
    Delivery:Mapped[Decimal]=mapped_column(Numeric(5,2),default=0.00)
    seller_id:Mapped[int]=mapped_column(Integer,
                                        ForeignKey("seller.id",
                                                   ondelete="CASCADE"),nullable=False
                                        )
    seller:Mapped["Seller"]=relationship("Seller",back_populates="delivery")
    