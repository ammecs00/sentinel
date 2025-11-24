"""
Enhanced Base client with offline queue system
"""

import time
import requests
import json
import logging
import socket
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import os
import queue
import pickle

from .config_manager import ConfigManager

class OfflineQueueManager:
    """Manages offline data storage and retransmission"""
    
    def __init__(self, storage_path: str, max_queue_size: int = 1000):
        self.storage_path = storage_path
        self.max_queue_size = max_queue_size
        self.queue_file = os.path.join(storage_path, 'offline_queue.pkl')
        self.lock = threading.Lock()
        
        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing queue
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from disk"""
        try:
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'rb') as f:
                    self._queue = pickle.load(f)
            else:
                self._queue = []
        except Exception as e:
            logging.warning(f"Failed to load queue: {e}")
            self._queue = []
    
    def _save_queue(self):
        """Save queue to disk"""
        try:
            with open(self.queue_file, 'wb') as f:
                pickle.dump(self._queue, f)
        except Exception as e:
            logging.error(f"Failed to save queue: {e}")
    
    def add_activity(self, activity_data: Dict[str, Any]):
        """Add activity to offline queue"""
        with self.lock:
            if len(self._queue) >= self.max_queue_size:
                # Remove oldest item if queue is full
                self._queue.pop(0)
            
            self._queue.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': activity_data
            })
            self._save_queue()
    
    def get_pending_activities(self) -> List[Dict[str, Any]]:
        """Get all pending activities"""
        with self.lock:
            return self._queue.copy()
    
    def remove_activities(self, count: int):
        """Remove activities from queue after successful send"""
        with self.lock:
            if count > 0:
                self._queue = self._queue[count:]
                self._save_queue()
    
    def clear_queue(self):
        """Clear the entire queue"""
        with self.lock:
            self._queue = []
            self._save_queue()
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self._queue)

class BaseMonitorClient(ABC):
    def __init__(self, config_path: str, client_type: str):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        self.client_type = client_type
        self.client_id = self.config.get('client_id', f"{client_type}-{self._get_hostname()}")
        self.server_url = self.config['server_url']
        self.api_key = self.config['api_key']
        self.interval = self.config.get('interval', 60)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 5)
        self.logger = logging.getLogger(client_type)
        
        # Initialize offline queue
        queue_storage = os.path.join(
            os.path.dirname(config_path), 
            'offline_storage'
        )
        self.offline_queue = OfflineQueueManager(queue_storage)
        
        # Connection state
        self.is_online = True
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        
    def _get_hostname(self) -> str:
        """Get system hostname"""
        return socket.gethostname().lower().replace(' ', '-')
    
    @abstractmethod
    def get_active_window(self) -> Optional[str]:
        """Get active window - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_process_list(self) -> list:
        """Get process list - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information - to be implemented by subclasses"""
        pass
    
    def get_additional_data(self) -> Dict[str, Any]:
        """Get additional data - can be overridden by subclasses"""
        return {}
    
    def collect_activity_data(self) -> Dict[str, Any]:
        """Collect comprehensive activity data"""
        try:
            data = {
                "client_id": self.client_id,
                "client_type": self.client_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active_window": self.get_active_window(),
                "processes": self.get_process_list(),
                "system_metrics": self.get_system_metrics(),
                "platform": self.get_platform_info(),
                "additional_data": self.get_additional_data()
            }
            
            # Filter out None values
            data = {k: v for k, v in data.items() if v is not None}
            
            self.logger.debug("Collected activity data")
            return data
        except Exception as e:
            self.logger.error(f"Error collecting activity data: {e}")
            return {}
    
    def flush_offline_queue(self) -> bool:
        """Send all pending activities from offline queue"""
        pending_activities = self.offline_queue.get_pending_activities()
        if not pending_activities:
            return True
        
        self.logger.info(f"Flushing {len(pending_activities)} pending activities from offline queue")
        
        successful_sends = 0
        for activity in pending_activities:
            if self._send_single_report(activity['data']):
                successful_sends += 1
            else:
                # Stop on first failure to maintain order
                break
        
        # Remove successfully sent activities
        if successful_sends > 0:
            self.offline_queue.remove_activities(successful_sends)
            self.logger.info(f"Successfully sent {successful_sends} queued activities")
        
        return successful_sends == len(pending_activities)
    
    def _send_single_report(self, data: Dict[str, Any]) -> bool:
        """Send a single activity report"""
        for attempt in range(self.max_retries):
            try:
                headers = {
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    f"{self.server_url}/api/v1/activities/report",
                    json=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return True
                elif response.status_code == 401:
                    self.logger.error("Invalid API key - check your configuration")
                    return False
                else:
                    self.logger.warning(f"Server returned error {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return False
                    
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False
            except requests.exceptions.Timeout:
                self.logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error sending report: {e}")
                return False
        
        return False
    
    def send_report(self, data: Dict[str, Any]) -> bool:
        """Send activity report with offline queue support"""
        # First, try to flush any pending activities
        if self.offline_queue.get_queue_size() > 0:
            if self.flush_offline_queue():
                self.is_online = True
                self.consecutive_failures = 0
            else:
                self.is_online = False
                self.consecutive_failures += 1
        
        # Try to send current data
        if self.is_online:
            success = self._send_single_report(data)
            if success:
                self.consecutive_failures = 0
                return True
            else:
                self.consecutive_failures += 1
                self.is_online = False
        
        # If offline or send failed, add to queue
        if not self.is_online:
            self.offline_queue.add_activity(data)
            queue_size = self.offline_queue.get_queue_size()
            self.logger.warning(f"Added activity to offline queue (size: {queue_size})")
            
            # Check if we should try to recover connection
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.logger.info("Attempting connection recovery...")
                time.sleep(self.interval * 2)  # Extended wait
                self.consecutive_failures = 0
        
        return self.is_online
    
    def run(self):
        """Main monitoring loop with offline support"""
        self.logger.info(f"Starting {self.client_type} Sentinel Client (ID: {self.client_id})")
        self.logger.info(f"Reporting to: {self.server_url}")
        self.logger.info(f"Interval: {self.interval} seconds")
        self.logger.info(f"Offline queue: {self.offline_queue.get_queue_size()} pending activities")
        self.logger.info("Press Ctrl+C to stop...")
        
        try:
            while True:
                try:
                    data = self.collect_activity_data()
                    if data:
                        success = self.send_report(data)
                        
                        if success:
                            self.logger.info(f"Report sent at {datetime.now().strftime('%H:%M:%S')}")
                        else:
                            self.logger.warning(f"Report queued offline (queue size: {self.offline_queue.get_queue_size()})")
                    else:
                        self.logger.warning("No data collected, skipping report")
                    
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.logger.info("Client stopped by user")
            # Final attempt to flush queue
            if self.offline_queue.get_queue_size() > 0:
                self.logger.info("Attempting to flush remaining queued activities...")
                self.flush_offline_queue()
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise