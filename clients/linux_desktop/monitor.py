#!/usr/bin/env python3
"""
Enhanced Sentinel Linux Desktop Client
Deep monitoring for browser usage, applications, and system activities
"""

import time
import argparse
import platform
import psutil
import requests
import json
import os
import subprocess
import sys
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import sqlite3
import configparser

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from base_client import BaseMonitorClient
from config_manager import ConfigManager
from utils import setup_logging, get_system_info

class LinuxDesktopClient(BaseMonitorClient):
    def __init__(self, config_path: str):
        super().__init__(config_path, "linux_desktop")
        self.logger = setup_logging("linux_desktop")
        self.last_window = None
        self.window_start_time = None
        self.application_usage = {}
        
    def get_active_window(self) -> Optional[str]:
        """Get active window with detailed information"""
        try:
            # Try xdotool first for window title
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                window_name = result.stdout.strip()
                
                # Get window class for better categorization
                try:
                    class_result = subprocess.run(
                        ['xdotool', 'getactivewindow', 'getwindowclassname'],
                        capture_output=True, text=True, timeout=1
                    )
                    window_class = class_result.stdout.strip() if class_result.returncode == 0 else "Unknown"
                except:
                    window_class = "Unknown"
                
                # Track window usage time
                current_time = time.time()
                if self.last_window != window_name:
                    if self.last_window and self.window_start_time:
                        duration = current_time - self.window_start_time
                        self._track_application_usage(self.last_window, duration)
                    
                    self.last_window = window_name
                    self.window_start_time = current_time
                
                return {
                    "title": window_name,
                    "class": window_class,
                    "focused": True
                }
        except Exception as e:
            self.logger.debug(f"Error getting active window: {e}")
        
        return None
    
    def _track_application_usage(self, window_title: str, duration: float):
        """Track application usage time"""
        app_name = self._extract_application_name(window_title)
        if app_name not in self.application_usage:
            self.application_usage[app_name] = 0
        self.application_usage[app_name] += duration
    
    def _extract_application_name(self, window_title: str) -> str:
        """Extract application name from window title"""
        # Common patterns for application names
        patterns = {
            'firefox': r'Firefox|Mozilla Firefox',
            'chrome': r'Google Chrome|Chromium',
            'code': r'Visual Studio Code|VSCode',
            'terminal': r'Terminal|GNOME Terminal|Konsole',
            'files': r'Files|Nautilus|Dolphin',
            'libreoffice': r'LibreOffice|Writer|Calc|Impress'
        }
        
        for app, pattern in patterns.items():
            if re.search(pattern, window_title, re.IGNORECASE):
                return app
        
        return "Unknown"
    
    def get_browser_usage(self) -> Dict[str, Any]:
        """Get detailed browser usage information"""
        browser_data = {}
        
        # Firefox tracking
        firefox_data = self._get_firefox_usage()
        if firefox_data:
            browser_data['firefox'] = firefox_data
        
        # Chrome/Chromium tracking
        chrome_data = self._get_chrome_usage()
        if chrome_data:
            browser_data['chrome'] = chrome_data
        
        return browser_data
    
    def _get_firefox_usage(self) -> Optional[Dict[str, Any]]:
        """Get Firefox browser usage data"""
        try:
            # Try to find Firefox profile
            home_dir = os.path.expanduser("~")
            firefox_dir = os.path.join(home_dir, '.mozilla', 'firefox')
            
            if os.path.exists(firefox_dir):
                profiles = []
                for item in os.listdir(firefox_dir):
                    if item.endswith('.default-release'):
                        profile_path = os.path.join(firefox_dir, item)
                        places_db = os.path.join(profile_path, 'places.sqlite')
                        
                        if os.path.exists(places_db):
                            # Get recent history (simplified - in production, handle DB carefully)
                            conn = sqlite3.connect(places_db)
                            cursor = conn.cursor()
                            
                            try:
                                cursor.execute("""
                                    SELECT url, title, visit_count, last_visit_date 
                                    FROM moz_places 
                                    ORDER BY last_visit_date DESC 
                                    LIMIT 20
                                """)
                                history = cursor.fetchall()
                                
                                profiles.append({
                                    'profile': item,
                                    'recent_history': [
                                        {
                                            'url': row[0],
                                            'title': row[1],
                                            'visit_count': row[2],
                                            'last_visit': row[3]
                                        } for row in history
                                    ]
                                })
                            except Exception as e:
                                self.logger.debug(f"Error reading Firefox history: {e}")
                            finally:
                                conn.close()
                
                return {
                    'profiles': profiles,
                    'tabs_count': self._get_firefox_tab_count()
                }
        except Exception as e:
            self.logger.debug(f"Error getting Firefox usage: {e}")
        
        return None
    
    def _get_firefox_tab_count(self) -> int:
        """Estimate Firefox tab count"""
        try:
            result = subprocess.run(
                ['pgrep', '-c', 'firefox'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except:
            pass
        return 0
    
    def _get_chrome_usage(self) -> Optional[Dict[str, Any]]:
        """Get Chrome/Chromium usage data"""
        try:
            home_dir = os.path.expanduser("~")
            chrome_dir = os.path.join(home_dir, '.config', 'google-chrome')
            chromium_dir = os.path.join(home_dir, '.config', 'chromium')
            
            browser_dirs = []
            if os.path.exists(chrome_dir):
                browser_dirs.append(('chrome', chrome_dir))
            if os.path.exists(chromium_dir):
                browser_dirs.append(('chromium', chromium_dir))
            
            browser_data = {}
            for browser_name, browser_dir in browser_dirs:
                profiles = []
                for item in os.listdir(browser_dir):
                    if item.startswith('Profile') or item == 'Default':
                        profile_path = os.path.join(browser_dir, item)
                        history_db = os.path.join(profile_path, 'History')
                        
                        if os.path.exists(history_db):
                            # Copy the database to avoid locking issues
                            import tempfile
                            import shutil
                            
                            with tempfile.NamedTemporaryFile(delete=False) as temp_db:
                                shutil.copy2(history_db, temp_db.name)
                                
                                try:
                                    conn = sqlite3.connect(temp_db.name)
                                    cursor = conn.cursor()
                                    
                                    cursor.execute("""
                                        SELECT url, title, visit_count, last_visit_time 
                                        FROM urls 
                                        ORDER BY last_visit_time DESC 
                                        LIMIT 20
                                    """)
                                    history = cursor.fetchall()
                                    
                                    profiles.append({
                                        'profile': item,
                                        'recent_history': [
                                            {
                                                'url': row[0],
                                                'title': row[1],
                                                'visit_count': row[2],
                                                'last_visit': row[3]
                                            } for row in history
                                        ]
                                    })
                                except Exception as e:
                                    self.logger.debug(f"Error reading {browser_name} history: {e}")
                                finally:
                                    conn.close()
                                os.unlink(temp_db.name)
                
                if profiles:
                    browser_data[browser_name] = {
                        'profiles': profiles,
                        'tabs_count': self._get_chrome_tab_count(browser_name)
                    }
            
            return browser_data
        except Exception as e:
            self.logger.debug(f"Error getting Chrome usage: {e}")
        
        return None
    
    def _get_chrome_tab_count(self, browser: str) -> int:
        """Estimate Chrome tab count"""
        try:
            result = subprocess.run(
                ['pgrep', '-c', browser],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except:
            pass
        return 0
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get detailed process information"""
        desktop_keywords = [
            'firefox', 'chrome', 'chromium', 'nautilus', 'gedit', 'libreoffice',
            'thunderbird', 'slack', 'discord', 'telegram', 'code', 'sublime',
            'terminal', 'gnome-terminal', 'konsole', 'xfce4-terminal', 'evolution',
            'outlook', 'skype', 'teams', 'zoom', 'signal', 'whatsapp', 'spotify',
            'steam', 'gimp', 'inkscape', 'blender', 'vlc', 'mpv'
        ]
        
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent', 'create_time', 'cmdline']):
                try:
                    # Filter for user processes (not system daemons)
                    if proc.info['username'] != 'root' and proc.info['pid'] > 1000:
                        proc_name = proc.info['name'].lower()
                        is_desktop_app = any(keyword in proc_name for keyword in desktop_keywords)
                        
                        if is_desktop_app:
                            process_info = {
                                "pid": proc.info['pid'],
                                "name": proc.info['name'],
                                "user": proc.info['username'],
                                "memory_rss_mb": round(proc.info['memory_info'].rss / (1024*1024), 1) if proc.info['memory_info'] else 0,
                                "cpu_percent": round(proc.info['cpu_percent'] or 0, 1),
                                "create_time": datetime.fromtimestamp(proc.info['create_time']).isoformat() if proc.info['create_time'] else None,
                                "cmdline": ' '.join(proc.info['cmdline'] or [])[:200] if proc.info['cmdline'] else '',
                                "is_desktop": True
                            }
                            processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError) as e:
                    self.logger.debug(f"Error accessing process: {e}")
                    continue
            
            # Limit to prevent huge payloads
            processes = processes[:50]
            self.logger.debug(f"Collected {len(processes)} desktop processes")
            return processes
        except Exception as e:
            self.logger.error(f"Error getting process list: {e}")
            return []
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/home') if os.path.exists('/home') else psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())
            
            # Battery info
            battery_info = None
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = {
                        "percent": round(battery.percent, 1),
                        "power_plugged": battery.power_plugged,
                        "time_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    }
            except Exception as e:
                self.logger.debug(f"Could not get battery info: {e}")
            
            # Temperature sensors
            temp_info = {}
            try:
                temperatures = psutil.sensors_temperatures()
                for name, entries in temperatures.items():
                    if entries:
                        temp_info[name] = {
                            'current': entries[0].current,
                            'high': entries[0].high,
                            'critical': entries[0].critical
                        }
            except Exception as e:
                self.logger.debug(f"Could not get temperature info: {e}")
            
            metrics = {
                "desktop_environment": os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown'),
                "session_type": os.environ.get('XDG_SESSION_TYPE', 'Unknown'),
                
                "cpu": {
                    "percent": round(cpu_percent, 1),
                    "per_core": [round(p, 1) for p in cpu_per_core],
                    "frequency_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
                    "cores": psutil.cpu_count(),
                    "load_average": os.getloadavg()
                },
                
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 1),
                    "used_gb": round(memory.used / (1024**3), 1),
                    "available_gb": round(memory.available / (1024**3), 1),
                    "percent": round(memory.percent, 1),
                    "swap_used_gb": round(swap.used / (1024**3), 1),
                    "swap_percent": round(swap.percent, 1) if swap.total > 0 else 0
                },
                
                "disk": {
                    "total_gb": round(disk_usage.total / (1024**3), 1),
                    "used_gb": round(disk_usage.used / (1024**3), 1),
                    "free_gb": round(disk_usage.free / (1024**3), 1),
                    "percent": round(disk_usage.percent, 1),
                    "read_mb": round(disk_io.read_bytes / (1024**2), 1) if disk_io else 0,
                    "write_mb": round(disk_io.write_bytes / (1024**2), 1) if disk_io else 0
                },
                
                "network": {
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 1),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 1),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "active_connections": net_connections
                },
                
                "battery": battery_info,
                "temperatures": temp_info,
                "users": len([u for u in psutil.users() if u.terminal]),
                "uptime_seconds": time.time() - psutil.boot_time()
            }
            
            self.logger.debug("Collected comprehensive system metrics")
            return metrics
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_additional_data(self) -> Dict[str, Any]:
        """Get additional desktop-specific data"""
        return {
            "browser_usage": self.get_browser_usage(),
            "application_usage": self.application_usage,
            "logged_in_users": self._get_logged_in_users(),
            "desktop_notifications": self._get_desktop_notifications(),
            "system_updates": self._get_system_updates_info()
        }
    
    def _get_logged_in_users(self) -> List[Dict[str, Any]]:
        """Get information about logged-in users"""
        users = []
        try:
            for user in psutil.users():
                users.append({
                    "name": user.name,
                    "terminal": user.terminal,
                    "host": user.host,
                    "started": datetime.fromtimestamp(user.started).isoformat()
                })
        except Exception as e:
            self.logger.debug(f"Error getting user info: {e}")
        
        return users
    
    def _get_desktop_notifications(self) -> Dict[str, Any]:
        """Get desktop notification status"""
        # This is a placeholder - actual implementation would depend on the desktop environment
        try:
            # Check if notification daemon is running
            result = subprocess.run(
                ['pgrep', '-f', 'notification'],
                capture_output=True, text=True
            )
            return {
                "daemon_running": result.returncode == 0,
                "daemon_name": "Unknown"  # Could be determined by checking process name
            }
        except:
            return {"daemon_running": False}
    
    def _get_system_updates_info(self) -> Dict[str, Any]:
        """Get system updates information"""
        update_info = {}
        
        # Check for Ubuntu/Debian updates
        try:
            result = subprocess.run(
                ['apt-get', 'update'],
                capture_output=True, text=True,
                timeout=30
            )
            if result.returncode == 0:
                upgrade_result = subprocess.run(
                    ['apt-get', 'upgrade', '--dry-run'],
                    capture_output=True, text=True
                )
                if upgrade_result.returncode == 0:
                    # Parse output to count updates
                    lines = upgrade_result.stdout.split('\n')
                    update_count = 0
                    for line in lines:
                        if 'upgraded,' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'upgraded,':
                                    update_count = int(parts[i-1])
                                    break
                    
                    update_info['apt'] = {
                        "updates_available": update_count,
                        "last_checked": datetime.now().isoformat()
                    }
        except Exception as e:
            self.logger.debug(f"Error checking system updates: {e}")
        
        return update_info
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform-specific information"""
        platform_info = get_system_info()
        platform_info.update({
            "client_type": "linux_desktop",
            "desktop_environment": os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown'),
            "session_type": os.environ.get('XDG_SESSION_TYPE', 'Unknown'),
            "display_manager": self._get_display_manager(),
            "window_manager": self._get_window_manager()
        })
        return platform_info
    
    def _get_display_manager(self) -> str:
        """Get display manager information"""
        try:
            result = subprocess.run(
                ['systemctl', 'status', 'display-manager'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Loaded:' in line:
                        return line.split('Loaded:')[1].split(';')[0].strip()
        except:
            pass
        return "Unknown"
    
    def _get_window_manager(self) -> str:
        """Get window manager information"""
        try:
            # Try different methods to detect window manager
            if 'GNOME' in os.environ.get('XDG_CURRENT_DESKTOP', ''):
                return "GNOME Shell"
            elif 'KDE' in os.environ.get('XDG_CURRENT_DESKTOP', ''):
                return "KDE Plasma"
            elif 'XFCE' in os.environ.get('XDG_CURRENT_DESKTOP', ''):
                return "XFCE"
            
            # Fallback to checking process
            wm_processes = ['gnome-shell', 'kwin_x11', 'kwin_wayland', 'xfwm4', 'mutter', 'compiz']
            for wm in wm_processes:
                result = subprocess.run(['pgrep', wm], capture_output=True)
                if result.returncode == 0:
                    return wm
        except:
            pass
        
        return "Unknown"

def main():
    parser = argparse.ArgumentParser(description="Enhanced Sentinel Linux Desktop Client")
    parser.add_argument(
        "--config", 
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    try:
        client = LinuxDesktopClient(args.config)
        if args.verbose:
            client.logger.setLevel("DEBUG")
        client.run()
    except KeyboardInterrupt:
        print("\nStopping Enhanced Linux Desktop Client...")
    except Exception as e:
        print(f"Failed to start client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()