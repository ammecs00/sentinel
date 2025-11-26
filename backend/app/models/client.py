from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), unique=True, index=True, nullable=False)
    client_type = Column(String(50), nullable=False)
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    platform_info = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Consent and compliance
    employee_consent = Column(Boolean, default=False, nullable=False)
    consent_date = Column(DateTime, nullable=True)
    consent_ip = Column(String(50), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = relationship("Activity", back_populates="client", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_clients_last_seen', 'last_seen'),
        Index('ix_clients_type_active', 'client_type', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Client(id={self.id}, client_id='{self.client_id}', type='{self.client_type}')>"