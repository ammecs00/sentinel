from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), ForeignKey('clients.client_id', ondelete='CASCADE'), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    
    # Activity data
    active_window = Column(Text, nullable=True)
    active_application = Column(String(255), nullable=True)
    active_url = Column(Text, nullable=True)
    
    # Process information
    processes = Column(Text, nullable=True)  # JSON string
    process_count = Column(Integer, default=0)
    
    # System metrics
    system_metrics = Column(Text, nullable=True)  # JSON string
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    disk_percent = Column(Float, nullable=True)
    
    # Categorization
    activity_category = Column(String(50), nullable=True)
    productivity_score = Column(Integer, nullable=True)
    
    # Additional data
    additional_data = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    client = relationship("Client", back_populates="activities")
    
    # Indexes
    __table_args__ = (
        Index('ix_activities_client_timestamp', 'client_id', 'timestamp'),
        Index('ix_activities_category', 'activity_category'),
    )
    
    def __repr__(self):
        return f"<Activity(id={self.id}, client_id='{self.client_id}', timestamp={self.timestamp})>"