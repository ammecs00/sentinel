from pydantic import BaseModel, validator, field_validator, constr
from typing import Optional, Dict, Any
from datetime import datetime
import json
import ipaddress


class ClientCreate(BaseModel):
    client_id: constr(min_length=1, max_length=255, pattern=r'^[a-zA-Z0-9_\-.:]+$')
    client_type: str
    hostname: Optional[constr(max_length=255)] = None
    ip_address: Optional[str] = None
    platform_info: Optional[Dict[str, Any]] = None
    employee_consent: bool = False

    @validator('client_type')
    def validate_client_type(cls, v):
        valid_types = ['linux_desktop', 'linux_server', 'windows_desktop', 'windows_server', 'macos_desktop']
        if v not in valid_types:
            raise ValueError(f'client_type must be one of {valid_types}')
        return v

    @validator('ip_address')
    def validate_ip_address(cls, v):
        if v:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v

    @validator('platform_info')
    def validate_platform_info_size(cls, v):
        if v and len(json.dumps(v)) > 5000:
            raise ValueError('Platform info too large')
        return v