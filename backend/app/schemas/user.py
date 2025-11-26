from pydantic import BaseModel, EmailStr, validator, constr
from typing import Optional
from datetime import datetime


class UserLogin(BaseModel):
    username: constr(min_length=1, max_length=50)
    password: str


class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    email: Optional[EmailStr] = None
    password: str
    is_admin: bool = False

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with _ or -)')
        return v