"""
Utility functions for Sentinel clients
"""

import logging
import platform
import os
import sys
from typing import Dict, Any

def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """Setup logging for the client"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set log level
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        try:
            log_dir = "/var/log/sentinel" if os.name == 'posix' else "C:\\Logs\\Sentinel"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, f"{name}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass  # Skip file logging if not possible
    
    return logger

def get_system_info() -> Dict[str, Any]:
    """Get basic system information"""
    try:
        import psutil
        
        # Get memory info
        memory = psutil.virtual_memory()
        
        # Get disk info
        disk = psutil.disk_usage('/' if os.name == 'posix' else 'C:\\')
        
        system_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "node": platform.node(),
            "architecture": platform.architecture()[0],
            "memory_total_gb": round(memory.total / (1024**3), 1),
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "python_version": platform.python_version()
        }
        
        # Add distribution info for Linux
        if hasattr(platform, 'linux_distribution'):
            distro = platform.linux_distribution()
            system_info["distribution"] = f"{distro[0]} {distro[1]}"
        elif os.path.exists('/etc/os-release'):
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            system_info["distribution"] = line.split('=', 1)[1].strip().strip('"')
                            break
            except:
                pass
        
        return system_info
        
    except Exception as e:
        # Fallback without psutil
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "node": platform.node(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version()
        }

def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Basic validation - API keys should start with "sk_" and be reasonably long
    return api_key.startswith("sk_") and len(api_key) > 20

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def is_connected() -> bool:
    """Check if system has internet connection"""
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False
