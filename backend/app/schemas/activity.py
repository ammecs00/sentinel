from pydantic import BaseModel, field_validator, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re


class ActivityCreate(BaseModel):
    client_id: str = Field(..., min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_\-.:]+$')
    timestamp: Optional[datetime] = None
    active_window: Optional[str] = Field(None, max_length=1000)
    active_application: Optional[str] = Field(None, max_length=255)
    active_url: Optional[str] = Field(None, max_length=2000)
    processes: Optional[List[Dict[str, Any]]] = None
    system_metrics: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None

    @field_validator('active_url')
    @classmethod
    def validate_url_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError('URL too long')
        return v

    @field_validator('processes')
    @classmethod
    def validate_processes_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError('Too many processes')
        return v

    @field_validator('system_metrics', 'additional_data')
    @classmethod
    def validate_json_size(cls, v):
        if v and len(json.dumps(v)) > 10000:
            raise ValueError('Data too large')
        return v