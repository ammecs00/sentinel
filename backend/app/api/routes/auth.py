from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user, get_current_admin_user
from app.models.user import User
from app.schemas.user import (
    UserLogin, UserCreate, UserOut, Token, ChangePassword
)
from app.schemas.api_key import ApiKeyCreate, ApiKeyOut, ApiKeyResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    auth_service = AuthService(db)
    user, error = auth_service.authenticate_user(
        user_data.username,
        user_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token_for_user(user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        force_password_change=user.force_password_change
    )


@router.post("/register", response_model=UserOut)
async def register(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Register new user (admin only)"""
    auth_service = AuthService(db)
    user, error = auth_service.create_user(
        username=user_data.username,
        password=user_data.password,
        email=user_data.email,
        is_admin=user_data.is_admin
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return user


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    auth_service = AuthService(db)
    success, error = auth_service.change_password(
        current_user,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "message": "Password changed successfully",
        "force_password_change": False
    }


@router.post("/keys", response_model=ApiKeyResponse)
async def create_api_key(
    key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create new API key (admin only)"""
    auth_service = AuthService(db)
    
    # Convert list of IPs to comma-separated string
    allowed_ips = ",".join(key_data.allowed_ips) if key_data.allowed_ips else None
    
    api_key, plain_key, error = auth_service.create_api_key(
        name=key_data.name,
        created_by=current_user.id,
        allowed_ips=allowed_ips,
        rate_limit=key_data.rate_limit,
        expires_at=key_data.expires_at
    )
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=plain_key,
        key_prefix=api_key.key_prefix,
        created_at=api_key.created_at
    )


@router.get("/keys", response_model=List[ApiKeyOut])
async def list_api_keys(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all API keys (admin only)"""
    auth_service = AuthService(db)
    return auth_service.list_api_keys()


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Revoke API key (admin only)"""
    auth_service = AuthService(db)
    success, error = auth_service.revoke_api_key(key_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )
    
    return {"message": "API key revoked successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout user (client-side token removal)"""
    return {"message": "Logged out successfully"}