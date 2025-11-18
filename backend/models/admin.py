from __future__ import annotations
from backend.database import Base
from sqlalchemy import Integer,String,Float,ForeignKey,Column,DateTime, func
from datetime import datetime
from sqlalchemy.orm import relationship,Mapped,mapped_column

class Admin(Base):
    
    __tablename__ = "admin"
    
    id : Mapped[int]=mapped_column(Integer, primary_key=True, index=True)
    username : Mapped[str]=mapped_column(String, unique=True, nullable=False)
    email : Mapped[str]=mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password : Mapped[str]=mapped_column(String, nullable=False)
    created_at : Mapped[DateTime]=mapped_column(DateTime, default=datetime.utcnow)
    updated_at : Mapped[DateTime]=mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role_name : Mapped[int] = mapped_column(ForeignKey("roles.role_name"), default="Admin")
    
    roles : Mapped["Roles"]=relationship("Roles",back_populates="admin")
    
    def __repr__(self)->str:
        return f"<Admin(username={self.username},email={self.email})>"