from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Float
from datetime import datetime
from app.core.database import Base


class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), index=True, nullable=False)
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
    activity_category = Column(String(50), nullable=True)  # work, break, idle, etc.
    productivity_score = Column(Integer, nullable=True)  # 0-100
    
    # Additional data
    additional_data = Column(Text, nullable=True)  # JSON string
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_activities_client_timestamp', 'client_id', 'timestamp'),
        Index('ix_activities_category', 'activity_category'),
        Index('ix_activities_timestamp_desc', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Activity(id={self.id}, client_id='{self.client_id}', timestamp={self.timestamp})>"