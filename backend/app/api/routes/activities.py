from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user, verify_api_key
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityOut, ActivityStats
from app.schemas.client import ClientCreate
from app.services.activity_service import ActivityService
from app.services.client_service import ClientService

router = APIRouter()


@router.post("/report")
async def report_activity(
    activity: ActivityCreate,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """
    Report client activity (protected by API key)
    This endpoint is used by monitoring clients to submit activity data
    """
    # Verify API key
    await verify_api_key(x_api_key, db)
    
    # Check if compliance mode is enabled
    if settings.REQUIRE_EMPLOYEE_CONSENT:
        client_service = ClientService(db)
        client = client_service.get_client(activity.client_id)
        
        # Only block if client exists and consent is explicitly missing
        if client and not client.employee_consent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee consent required for monitoring. Please contact administrator."
            )
    
    # Update or create client
    client_service = ClientService(db)
    client_data = ClientCreate(
        client_id=activity.client_id,
        client_type="unknown",
        employee_consent=False
    )
    
    # Extract client info from additional_data if available
    if activity.additional_data:
        client_data.client_type = activity.additional_data.get('client_type', 'unknown')
        client_data.hostname = activity.additional_data.get('hostname')
        client_data.ip_address = activity.additional_data.get('ip_address')
        client_data.platform_info = activity.additional_data.get('platform_info')
    
    client, is_new = client_service.create_or_update_client(client_data)
    
    # Create activity record
    activity_service = ActivityService(db)
    new_activity, error = activity_service.create_activity(activity)
    
    if not new_activity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "status": "success",
        "message": "Activity recorded successfully",
        "activity_id": new_activity.id,
        "new_client": is_new
    }


@router.get("/", response_model=List[ActivityOut])
async def get_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    client_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activities with filtering and pagination"""
    activity_service = ActivityService(db)
    activities = activity_service.get_activities(
        skip=skip,
        limit=limit,
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        category=category
    )
    # Pydantic handles JSON parsing automatically now
    return activities


@router.get("/stats", response_model=ActivityStats)
async def get_activity_stats(
    client_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity statistics"""
    activity_service = ActivityService(db)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    stats = activity_service.get_activity_stats(
        client_id=client_id,
        start_date=start_date
    )
    
    return ActivityStats(**stats)


@router.get("/{activity_id}", response_model=ActivityOut)
async def get_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific activity by ID"""
    activity_service = ActivityService(db)
    activity = activity_service.get_activity(activity_id)
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    return activity


@router.post("/cleanup")
async def cleanup_old_activities(
    days: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cleanup activities older than specified days (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    activity_service = ActivityService(db)
    deleted_count = activity_service.cleanup_old_activities(days=days)
    
    return {
        "message": f"Cleanup completed",
        "deleted_count": deleted_count,
        "retention_days": days
    }