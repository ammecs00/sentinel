from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime


class ApiKeyCreate(BaseModel):
    name: str
    allowed_ips: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    
    @validator('name')
    def name_length(cls, v):
        if len(v) < 3 or len(v) > 255:
            raise ValueError('Name must be between 3 and 255 characters')
        return v


class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    last_used: Optional[datetime] = None
    usage_count: int
    allowed_ips: Optional[str] = None
    rate_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApiKeyResponse(BaseModel):
    """Response when creating a new API key - includes full key"""
    id: int
    name: str
    key: str  # Full API key - only shown once
    key_prefix: str
    created_at: datetime
    
    class Config:
        from_attributes = True