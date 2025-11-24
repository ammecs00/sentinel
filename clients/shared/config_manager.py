"""
Configuration management for Sentinel clients
"""

import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['server_url', 'api_key']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required config field: {field}")
            
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config: {e}")
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure"""
        try:
            required_fields = ['server_url', 'api_key']
            for field in required_fields:
                if field not in config:
                    return False
            
            # Validate URL format
            if not config['server_url'].startswith(('http://', 'https://')):
                return False
            
            # Validate interval
            if 'interval' in config and (not isinstance(config['interval'], int) or config['interval'] < 10):
                return False
            
            return True
        except:
            return False
    
    def create_default_config(self, server_url: str, api_key: str, client_id: str = None) -> Dict[str, Any]:
        """Create a default configuration"""
        import socket
        if client_id is None:
            client_id = f"client-{socket.gethostname().lower().replace(' ', '-')}"
        
        return {
            "server_url": server_url,
            "api_key": api_key,
            "client_id": client_id,
            "interval": 60,
            "max_retries": 3,
            "retry_delay": 5,
            "log_level": "INFO",
            "features": {
                "track_active_window": True,
                "track_processes": True,
                "track_system_metrics": True
            }
        }
