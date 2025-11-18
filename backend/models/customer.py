from __future__ import annotations
from backend.database import Base
from sqlalchemy import Integer,String,Float,ForeignKey,Column,DateTime, func
from datetime import datetime
from sqlalchemy.orm import relationship,Mapped,mapped_column

class Customer(Base):
    
    __tablename__ = "customer"
    
    id : Mapped[int]=mapped_column(Integer, primary_key=True, index=True)
    username : Mapped[str]=mapped_column(String, unique=True, nullable=False)
    email : Mapped[str]=mapped_column(String, unique=True, index=True, nullable=False)
    phone_number:Mapped[int]=mapped_column(String, nullable=False)
    hashed_password : Mapped[str]=mapped_column(String, nullable=False)
    address:Mapped[str]=mapped_column(String,nullable=False)
    created_at : Mapped[DateTime]=mapped_column(DateTime, default=datetime.utcnow)
    updated_at : Mapped[DateTime]=mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status : Mapped[bool]=mapped_column(String, default=True)
    role_name : Mapped[int] = mapped_column(ForeignKey("roles.role_name"), default="Customer")
    
    role : Mapped["Roles"]=relationship("Roles",back_populates="users")
    # orders: Mapped[list["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")   
    # products: Mapped[list["Product"]] = relationship("Product", back_populates="user")
    # reviews: Mapped[list["Review"]] = relationship("Review", back_populates="user")
    
    def __repr__(self)->str:
        return f"<User(username={self.username},email={self.email})>"



