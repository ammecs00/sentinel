from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import logging
import html
import re

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
    
    def _categorize_activity(self, window: Optional[str], application: Optional[str], url: Optional[str]) -> str:
        """Categorize activity based on window, application, and URL"""
        # Simple categorization logic - you can expand this
        if not any([window, application, url]):
            return "unknown"
        
        text = f"{window or ''} {application or ''} {url or ''}".lower()
        
        # Productivity applications
        productivity_keywords = ['code', 'visual studio', 'pycharm', 'terminal', 'cmd', 'powershell',
                               'outlook', 'email', 'slack', 'teams', 'zoom', 'meet', 'confluence', 'jira']
        
        # Entertainment/leisure
        entertainment_keywords = ['youtube', 'netflix', 'facebook', 'instagram', 'twitter', 'tiktok',
                                'game', 'spotify', 'music', 'movie']
        
        # System/utility
        system_keywords = ['settings', 'control panel', 'file explorer', 'finder', 'task manager']
        
        for keyword in productivity_keywords:
            if keyword in text:
                return "productive"
        
        for keyword in entertainment_keywords:
            if keyword in text:
                return "entertainment"
        
        for keyword in system_keywords:
            if keyword in text:
                return "system"
        
        return "neutral"
    
    def _calculate_productivity_score(self, category: str, process_count: int, cpu_percent: Optional[float]) -> int:
        """Calculate productivity score based on various factors"""
        score = 50  # Default neutral score
        
        # Adjust based on category
        if category == "productive":
            score += 30
        elif category == "entertainment":
            score -= 20
        elif category == "system":
            score += 10
        
        # Adjust based on system load (moderate load is often productive)
        if cpu_percent is not None:
            if 20 <= cpu_percent <= 80:
                score += 10
            elif cpu_percent > 90:
                score -= 10
        
        # Adjust based on number of processes (too many might indicate inefficiency)
        if process_count > 50:
            score -= 10
        elif process_count < 10:
            score += 5
        
        return max(0, min(100, score))
    
    def get_activities(
        self,
        skip: int = 0,
        limit: int = 100,
        client_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> List[Activity]:
        """Get activities with filtering and pagination"""
        query = self.db.query(Activity)
        
        if client_id:
            query = query.filter(Activity.client_id == client_id)
        
        if start_date:
            query = query.filter(Activity.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Activity.timestamp <= end_date)
        
        if category:
            query = query.filter(Activity.activity_category == category)
        
        return query.order_by(desc(Activity.timestamp)).offset(skip).limit(limit).all()
    
    def get_activity(self, activity_id: int) -> Optional[Activity]:
        """Get specific activity by ID"""
        return self.db.query(Activity).filter(Activity.id == activity_id).first()
    
    def get_activity_stats(
        self,
        client_id: Optional[str] = None,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get activity statistics"""
        query = self.db.query(Activity)
        
        if client_id:
            query = query.filter(Activity.client_id == client_id)
        
        if start_date:
            query = query.filter(Activity.timestamp >= start_date)
        
        total_activities = query.count()
        
        # Get activities by category
        category_stats = self.db.query(
            Activity.activity_category,
            func.count(Activity.id)
        )
        
        if client_id:
            category_stats = category_stats.filter(Activity.client_id == client_id)
        if start_date:
            category_stats = category_stats.filter(Activity.timestamp >= start_date)
        
        category_stats = category_stats.group_by(Activity.activity_category).all()
        
        # Get active clients
        active_clients_query = self.db.query(func.count(func.distinct(Activity.client_id)))
        if start_date:
            active_clients_query = active_clients_query.filter(Activity.timestamp >= start_date)
        
        active_clients = active_clients_query.scalar() or 0
        
        # Average productivity score
        avg_score = self.db.query(func.avg(Activity.productivity_score))
        if client_id:
            avg_score = avg_score.filter(Activity.client_id == client_id)
        if start_date:
            avg_score = avg_score.filter(Activity.timestamp >= start_date)
        
        avg_score = avg_score.scalar() or 0
        
        return {
            "total_activities": total_activities,
            "active_clients": active_clients,
            "activities_by_category": dict(category_stats),
            "average_productivity_score": round(float(avg_score), 2)
        }
    
    def cleanup_old_activities(self, days: int = 90) -> int:
        """Cleanup activities older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = self.db.query(Activity).filter(Activity.timestamp < cutoff_date).delete()
        self.db.commit()
        
        logger.info(f"Cleaned up {result} activities older than {days} days")
        return result