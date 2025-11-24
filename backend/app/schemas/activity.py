from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class ActivityCreate(BaseModel):
    client_id: str
    timestamp: Optional[datetime] = None
    active_window: Optional[str] = None
    active_application: Optional[str] = None
    active_url: Optional[str] = None
    processes: Optional[List[Dict[str, Any]]] = None
    system_metrics: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None


class ActivityOut(BaseModel):
    id: int
    client_id: str
    timestamp: datetime
    active_window: Optional[str] = None
    active_application: Optional[str] = None
    active_url: Optional[str] = None
    processes: Optional[List[Dict[str, Any]]] = None
    process_count: int
    system_metrics: Optional[Dict[str, Any]] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    activity_category: Optional[str] = None
    productivity_score: Optional[int] = None
    
    @field_validator('processes', 'system_metrics', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    class Config:
        from_attributes = True


class ActivityStats(BaseModel):
    total_activities: int
    active_clients: int
    avg_cpu: Optional[float] = None
    avg_memory: Optional[float] = None
    top_applications: List[Dict[str, Any]] = []
    productivity_breakdown: Dict[str, int] = {}