from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from backend.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # "Admin" | "Seller" | "Customer"
    owner_id = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
