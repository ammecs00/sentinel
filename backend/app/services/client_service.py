from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import json
import logging

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate

logger = logging.getLogger(__name__)


class ClientService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        return self.db.query(Client).filter(Client.client_id == client_id).first()
    
    def get_clients(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        client_type: Optional[str] = None
    ) -> List[Client]:
        """Get clients with filtering"""
        query = self.db.query(Client)
        
        if is_active is not None:
            query = query.filter(Client.is_active == is_active)
        
        if client_type:
            query = query.filter(Client.client_type == client_type)
        
        return query.order_by(Client.last_seen.desc()).offset(skip).limit(limit).all()
    
    def create_or_update_client(
        self,
        client_data: ClientCreate
    ) -> Tuple[Client, bool]:
        """
        Create or update client
        Returns: (client, is_new)
        """
        client = self.get_client(client_data.client_id)
        is_new = False
        
        try:
            if client:
                # Update existing client
                client.last_seen = datetime.utcnow()
                if client_data.hostname:
                    client.hostname = client_data.hostname
                if client_data.ip_address:
                    client.ip_address = client_data.ip_address
                if client_data.platform_info:
                    client.platform_info = json.dumps(client_data.platform_info)
                if client_data.employee_consent:
                    if not client.employee_consent:
                        client.employee_consent = True
                        client.consent_date = datetime.utcnow()
                        client.consent_ip = client_data.ip_address
            else:
                # Create new client
                is_new = True
                client = Client(
                    client_id=client_data.client_id,
                    client_type=client_data.client_type,
                    hostname=client_data.hostname,
                    ip_address=client_data.ip_address,
                    platform_info=json.dumps(client_data.platform_info) if client_data.platform_info else None,
                    employee_consent=client_data.employee_consent,
                    consent_date=datetime.utcnow() if client_data.employee_consent else None,
                    consent_ip=client_data.ip_address if client_data.employee_consent else None,
                    is_active=True
                )
                self.db.add(client)
            
            self.db.commit()
            self.db.refresh(client)
            
            if is_new:
                logger.info(f"New client registered: {client.client_id}")
            
            return client, is_new
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating/updating client: {e}")
            raise
    
    def update_client(
        self,
        client_id: str,
        update_data: ClientUpdate
    ) -> Tuple[Optional[Client], str]:
        """
        Update client
        Returns: (client, error_message)
        """
        client = self.get_client(client_id)
        if not client:
            return None, "Client not found"
        
        try:
            if update_data.hostname is not None:
                client.hostname = update_data.hostname
            if update_data.ip_address is not None:
                client.ip_address = update_data.ip_address
            if update_data.platform_info is not None:
                client.platform_info = json.dumps(update_data.platform_info)
            if update_data.is_active is not None:
                client.is_active = update_data.is_active
            if update_data.employee_consent is not None and update_data.employee_consent:
                if not client.employee_consent:
                    client.employee_consent = True
                    client.consent_date = datetime.utcnow()
            
            client.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(client)
            
            logger.info(f"Client updated: {client_id}")
            return client, ""
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating client: {e}")
            return None, "Error updating client"
    
    def delete_client(self, client_id: str) -> Tuple[bool, str]:
        """
        Delete client
        Returns: (success, error_message)
        """
        client = self.get_client(client_id)
        if not client:
            return False, "Client not found"
        
        try:
            self.db.delete(client)
            self.db.commit()
            logger.info(f"Client deleted: {client_id}")
            return True, ""
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting client: {e}")
            return False, "Error deleting client"
    
    def get_online_clients(self, minutes: int = 5) -> List[Client]:
        """Get clients that were active in the last N minutes"""
        threshold = datetime.utcnow() - timedelta(minutes=minutes)
        return self.db.query(Client).filter(
            Client.last_seen >= threshold,
            Client.is_active == True
        ).all()
    
    def get_client_count(self) -> int:
        """Get total client count"""
        return self.db.query(Client).filter(Client.is_active == True).count()