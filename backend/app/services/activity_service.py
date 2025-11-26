from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import logging
import html

from app.models.activity import Activity
from app.schemas.activity import ActivityCreate

logger = logging.getLogger(__name__)


class ActivityService:
    def __init__(self, db: Session):
        self.db = db
    
    def sanitize_string(self, text: Optional[str]) -> Optional[str]:
        """Sanitize string input to prevent XSS"""
        if not text:
            return None
        # Escape HTML characters
        return html.escape(text.strip())[:10000]  # Limit length
    
    def create_activity(self, activity_data: ActivityCreate) -> Tuple[Optional[Activity], str]:
        """
        Create new activity record with input sanitization
        Returns: (activity, error_message)
        """
        try:
            # Sanitize inputs
            sanitized_window = self.sanitize_string(activity_data.active_window)
            sanitized_application = self.sanitize_string(activity_data.active_application)
            sanitized_url = self.sanitize_string(activity_data.active_url)
            
            # Validate client_id format
            if not re.match(r'^[a-zA-Z0-9_\-.:]+$', activity_data.client_id):
                return None, "Invalid client ID format"
            
            # Extract metrics
            cpu_percent = None
            memory_percent = None
            disk_percent = None
            
            if activity_data.system_metrics:
                # Validate system metrics values
                cpu_percent = min(max(0, activity_data.system_metrics.get('cpu_percent', 0)), 100)
                memory_percent = min(max(0, activity_data.system_metrics.get('memory_percent', 0)), 100)
                disk_percent = min(max(0, activity_data.system_metrics.get('disk_percent', 0)), 100)
            
            # Validate process count
            process_count = len(activity_data.processes) if activity_data.processes else 0
            if process_count > 1000:
                process_count = 1000  # Cap at reasonable limit
            
            # Categorize activity
            category = self._categorize_activity(sanitized_window, sanitized_application, sanitized_url)
            
            # Calculate productivity score
            productivity_score = self._calculate_productivity_score(category, process_count, cpu_percent)
            
            activity = Activity(
                client_id=activity_data.client_id,
                timestamp=activity_data.timestamp or datetime.utcnow(),
                active_window=sanitized_window,
                active_application=sanitized_application,
                active_url=sanitized_url,
                processes=json.dumps(activity_data.processes[:100]) if activity_data.processes else None,  # Limit processes
                process_count=process_count,
                system_metrics=json.dumps(activity_data.system_metrics) if activity_data.system_metrics else None,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                activity_category=category,
                productivity_score=productivity_score,
                additional_data=json.dumps(activity_data.additional_data) if activity_data.additional_data else None
            )
            
            self.db.add(activity)
            self.db.commit()
            self.db.refresh(activity)
            
            return activity, ""
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating activity: {e}")
            return None, "Error creating activity"
    
    # ... rest of the class remains the same ...