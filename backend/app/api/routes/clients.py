from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.client import ClientOut, ClientUpdate
from app.services.client_service import ClientService

router = APIRouter()


@router.get("/", response_model=List[ClientOut])
async def get_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    client_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all clients with filtering and pagination"""
    client_service = ClientService(db)
    clients = client_service.get_clients(
        skip=skip,
        limit=limit,
        is_active=is_active,
        client_type=client_type
    )
    # Pydantic handles JSON parsing automatically
    return clients


@router.get("/online", response_model=List[ClientOut])
async def get_online_clients(
    minutes: int = Query(5, ge=1, le=60),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get clients that were active in the last N minutes"""
    client_service = ClientService(db)
    clients = client_service.get_online_clients(minutes=minutes)
    return clients


@router.get("/stats")
async def get_client_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get client statistics"""
    client_service = ClientService(db)
    
    total_clients = client_service.get_client_count()
    online_clients = len(client_service.get_online_clients(minutes=5))
    
    # Get clients by type
    clients_by_type = {}
    for client_type in ['linux_desktop', 'linux_server', 'windows_desktop', 'windows_server', 'macos_desktop']:
        count = len(client_service.get_clients(client_type=client_type, limit=1000))
        if count > 0:
            clients_by_type[client_type] = count
    
    return {
        "total_clients": total_clients,
        "online_clients": online_clients,
        "offline_clients": total_clients - online_clients,
        "clients_by_type": clients_by_type
    }


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific client by ID"""
    client_service = ClientService(db)
    client = client_service.get_client(client_id)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return client


@router.put("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: str,
    update_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update client information"""
    client_service = ClientService(db)
    client, error = client_service.update_client(client_id, update_data)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )
    
    return client


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete client and all associated activities"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    client_service = ClientService(db)
    success, error = client_service.delete_client(client_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )
    
    return {"message": "Client deleted successfully"}