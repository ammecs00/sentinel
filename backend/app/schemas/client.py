from pydantic import BaseModel, validator, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import json


class ClientCreate(BaseModel):
    client_id: str
    client_type: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    platform_info: Optional[Dict[str, Any]] = None
    employee_consent: bool = False
    
    @validator('client_type')
    def validate_client_type(cls, v):
        valid_types = ['linux_desktop', 'linux_server', 'windows_desktop', 'windows_server', 'macos_desktop']
        if v not in valid_types:
            raise ValueError(f'client_type must be one of {valid_types}')
        return v


class ClientUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    platform_info: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    employee_consent: Optional[bool] = None


class ClientOut(BaseModel):
    id: int
    client_id: str
    client_type: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    platform_info: Optional[Dict[str, Any]] = None
    is_active: bool
    last_seen: datetime
    employee_consent: bool
    consent_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    @field_validator('platform_info', mode='before')
    @classmethod
    def parse_platform_info(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    class Config:
        from_attributes = True