from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import logging

from app.models.activity import Activity
from app.schemas.activity import ActivityCreate

logger = logging.getLogger(__name__)


class ActivityService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_activity(self, activity_data: ActivityCreate) -> Tuple[Optional[Activity], str]:
        """
        Create new activity record
        Returns: (activity, error_message)
        """
        try:
            # Extract metrics for indexing
            cpu_percent = None
            memory_percent = None
            disk_percent = None
            
            if activity_data.system_metrics:
                cpu_percent = activity_data.system_metrics.get('cpu_percent')
                memory_percent = activity_data.system_metrics.get('memory_percent')
                disk_percent = activity_data.system_metrics.get('disk_percent')
            
            # Count processes
            process_count = len(activity_data.processes) if activity_data.processes else 0
            
            # Categorize activity
            category = self._categorize_activity(
                activity_data.active_window,
                activity_data.active_application,
                activity_data.active_url
            )
            
            # Calculate productivity score
            productivity_score = self._calculate_productivity_score(
                category,
                process_count,
                cpu_percent
            )
            
            activity = Activity(
                client_id=activity_data.client_id,
                timestamp=activity_data.timestamp or datetime.utcnow(),
                active_window=activity_data.active_window,
                active_application=activity_data.active_application,
                active_url=activity_data.active_url,
                processes=json.dumps(activity_data.processes) if activity_data.processes else None,
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
    
    def get_activity(self, activity_id: int) -> Optional[Activity]:
        """Get activity by ID"""
        return self.db.query(Activity).filter(Activity.id == activity_id).first()
    
    def get_activities(
        self,
        skip: int = 0,
        limit: int = 100,
        client_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> List[Activity]:
        """Get activities with filtering"""
        query = self.db.query(Activity)
        
        if client_id:
            query = query.filter(Activity.client_id == client_id)
        
        if start_date:
            query = query.filter(Activity.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Activity.timestamp <= end_date)
        
        if category:
            query = query.filter(Activity.activity_category == category)
        
        return query.order_by(Activity.timestamp.desc()).offset(skip).limit(limit).all()
    
    def get_activity_stats(
        self,
        client_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get activity statistics"""
        query = self.db.query(Activity)
        
        if client_id:
            query = query.filter(Activity.client_id == client_id)
        
        if start_date:
            query = query.filter(Activity.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Activity.timestamp <= end_date)
        
        total = query.count()
        
        # Average metrics
        avg_cpu = query.with_entities(func.avg(Activity.cpu_percent)).scalar()
        avg_memory = query.with_entities(func.avg(Activity.memory_percent)).scalar()
        avg_productivity = query.with_entities(func.avg(Activity.productivity_score)).scalar()
        
        # Top applications
        top_apps = query.filter(Activity.active_application.isnot(None)).with_entities(
            Activity.active_application,
            func.count(Activity.id).label('count')
        ).group_by(Activity.active_application).order_by(desc('count')).limit(10).all()
        
        # Category breakdown
        category_stats = query.filter(Activity.activity_category.isnot(None)).with_entities(
            Activity.activity_category,
            func.count(Activity.id).label('count')
        ).group_by(Activity.activity_category).all()
        
        # Active clients
        active_clients = query.with_entities(
            func.count(func.distinct(Activity.client_id))
        ).scalar()
        
        return {
            'total_activities': total,
            'active_clients': active_clients or 0,
            'avg_cpu': round(avg_cpu, 2) if avg_cpu else None,
            'avg_memory': round(avg_memory, 2) if avg_memory else None,
            'avg_productivity': round(avg_productivity, 2) if avg_productivity else None,
            'top_applications': [
                {'application': app, 'count': count}
                for app, count in top_apps
            ],
            'category_breakdown': {
                category: count
                for category, count in category_stats
            }
        }
    
    def cleanup_old_activities(self, days: int = 90) -> int:
        """Delete activities older than specified days"""
        threshold = datetime.utcnow() - timedelta(days=days)
        
        try:
            deleted = self.db.query(Activity).filter(
                Activity.timestamp < threshold
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted} old activities")
            return deleted
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up activities: {e}")
            return 0
    
    def _categorize_activity(
        self,
        window: Optional[str],
        application: Optional[str],
        url: Optional[str]
    ) -> str:
        """Categorize activity based on context"""
        if not window and not application:
            return 'idle'
        
        # Work-related keywords
        work_keywords = [
            'vscode', 'visual studio', 'pycharm', 'intellij', 'eclipse',
            'terminal', 'cmd', 'powershell', 'bash',
            'excel', 'word', 'powerpoint', 'outlook',
            'slack', 'teams', 'zoom', 'meet',
            'jira', 'confluence', 'github', 'gitlab'
        ]
        
        # Break/personal keywords
        break_keywords = [
            'youtube', 'facebook', 'twitter', 'instagram', 'reddit',
            'netflix', 'spotify', 'steam', 'game'
        ]
        
        text = f"{window or ''} {application or ''} {url or ''}".lower()
        
        if any(keyword in text for keyword in work_keywords):
            return 'work'
        elif any(keyword in text for keyword in break_keywords):
            return 'break'
        else:
            return 'other'
    
    def _calculate_productivity_score(
        self,
        category: str,
        process_count: int,
        cpu_percent: Optional[float]
    ) -> int:
        """Calculate productivity score (0-100)"""
        score = 50  # Base score
        
        # Category impact
        if category == 'work':
            score += 30
        elif category == 'break':
            score -= 20
        elif category == 'idle':
            score -= 30
        
        # Process count impact
        if process_count > 20:
            score += 10
        elif process_count < 5:
            score -= 10
        
        # CPU usage impact
        if cpu_percent:
            if 20 <= cpu_percent <= 70:
                score += 10  # Active work
            elif cpu_percent > 90:
                score -= 10  # System overload
        
        # Clamp between 0 and 100
        return max(0, min(100, score))