from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime,Column
from sqlalchemy.orm import relationship,Mapped
from backend.database import Base

class Roles(Base):
    
    __tablename__="roles"
    id=Column(Integer,index=True,primary_key=True,nullable=False)
    role_name=Column(String,unique=True,nullable=False)
    descripted=Column(String)
    
    users :Mapped[list["User"]]=relationship("User",back_populates="role")
    
    def __repr__(self)->str:
        return f"<Role(id={self.id},role_name={self.role_name})>"