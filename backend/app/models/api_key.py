from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Restrictions
    allowed_ips = Column(Text, nullable=True)
    rate_limit = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    creator = relationship("User")
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}', active={self.is_active})>"