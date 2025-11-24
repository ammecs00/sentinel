#!/usr/bin/env python3
"""
Enhanced Sentinel Windows Desktop Client
Deep monitoring for Windows desktop environments with comprehensive application tracking
"""

import time
import argparse
import platform
import psutil
import requests
import json
import os
import sys
import subprocess
import winreg
import threading
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import sqlite3
import tempfile
import shutil

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from base_client import BaseMonitorClient
from config_manager import ConfigManager
from utils import setup_logging, get_system_info

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    import win32evtlog
    import win32security
    import pythoncom
    import wmi
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("Warning: pywin32 not available. Some advanced features disabled.")

class WindowsDesktopClient(BaseMonitorClient):
    def __init__(self, config_path: str):
        super().__init__(config_path, "windows_desktop")
        self.logger = setup_logging("windows_desktop")
        self.last_window = None
        self.window_start_time = None
        self.application_usage = {}
        self.browser_monitor = BrowserMonitor(self.logger)
        
        # Initialize WMI for advanced system monitoring
        self.wmi_conn = None
        if HAS_WIN32:
            try:
                pythoncom.CoInitialize()
                self.wmi_conn = wmi.WMI()
            except Exception as e:
                self.logger.warning(f"Failed to initialize WMI: {e}")
    
    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get active window with detailed information"""
        if not HAS_WIN32:
            self.logger.debug("pywin32 not available, window tracking disabled")
            return None
            
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                window_title = win32gui.GetWindowText(hwnd)
                
                # Get process information
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                    process_path = process.exe()
                    
                    # Get window class
                    window_class = win32gui.GetClassName(hwnd)
                    
                    # Get window placement
                    placement = win32gui.GetWindowPlacement(hwnd)
                    
                    # Track window usage time
                    current_time = time.time()
                    window_key = f"{process_name}|{window_title}"
                    
                    if self.last_window != window_key:
                        if self.last_window and self.window_start_time:
                            duration = current_time - self.window_start_time
                            self._track_application_usage(self.last_window, duration)
                        
                        self.last_window = window_key
                        self.window_start_time = current_time
                    
                    window_info = {
                        "title": window_title,
                        "process_name": process_name,
                        "process_path": process_path,
                        "process_id": pid,
                        "window_class": window_class,
                        "placement": {
                            "show_cmd": placement[1],
                            "min_position": placement[2],
                            "max_position": placement[3],
                            "normal_position": placement[4]
                        },
                        "focused": True
                    }
                    
                    self.logger.debug(f"Active window: {process_name} - {window_title}")
                    return window_info
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.logger.debug(f"Could not access process for window: {window_title}")
                    return {"title": window_title, "process_name": "Unknown"}
                    
        except Exception as e:
            self.logger.debug(f"Error getting active window: {e}")
        
        return None
    
    def _track_application_usage(self, window_key: str, duration: float):
        """Track application usage time"""
        if window_key not in self.application_usage:
            self.application_usage[window_key] = 0
        self.application_usage[window_key] += duration
    
    def get_browser_usage(self) -> Dict[str, Any]:
        """Get detailed browser usage information"""
        return self.browser_monitor.get_browser_usage()
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get detailed process information for desktop applications"""
        desktop_keywords = [
            'chrome', 'firefox', 'edge', 'msedge', 'explorer', 'notepad', 
            'word', 'excel', 'powerpoint', 'outlook', 'teams', 'slack', 
            'discord', 'code', 'vscode', 'sublime_text', 'notepad++',
            'spotify', 'steam', 'photoshop', 'illustrator', 'acrobat',
            'calculator', 'paint', 'mspaint', 'winword', 'excel', 'powerpnt',
            'outlook', 'thunderbird', 'telegram', 'whatsapp', 'signal',
            'skype', 'zoom', 'teams', 'cmd', 'powershell', 'windowsterminal'
        ]
        
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent', 'create_time', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower().replace('.exe', '')
                    is_desktop_app = any(keyword in proc_name for keyword in desktop_keywords)
                    
                    # Also include processes with windows
                    has_window = self._process_has_window(proc.info['pid'])
                    
                    if is_desktop_app or has_window:
                        process_info = {
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "user": proc.info['username'],
                            "memory_rss_mb": round(proc.info['memory_info'].rss / (1024*1024), 1) if proc.info['memory_info'] else 0,
                            "cpu_percent": round(proc.info['cpu_percent'] or 0, 1),
                            "create_time": datetime.fromtimestamp(proc.info['create_time']).isoformat() if proc.info['create_time'] else None,
                            "cmdline": ' '.join(proc.info['cmdline'] or [])[:200] if proc.info['cmdline'] else '',
                            "has_window": has_window,
                            "is_system": 'SYSTEM' in proc.info['username'] or 'NETWORK SERVICE' in proc.info['username']
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
    
    def _process_has_window(self, pid: int) -> bool:
        """Check if process has visible windows"""
        if not HAS_WIN32:
            return False
            
        try:
            def enum_windows_proc(hwnd, param):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        param['has_window'] = True
                        return False  # Stop enumeration
                return True
            
            param = {'has_window': False}
            win32gui.EnumWindows(enum_windows_proc, param)
            return param['has_window']
        except:
            return False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive Windows system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics - multiple drives
            disk_info = {}
            for partition in psutil.disk_partitions():
                try:
                    if 'cdrom' in partition.opts:
                        continue
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_io = psutil.disk_io_counters(perdisk=True)
                    
                    disk_info[partition.mountpoint] = {
                        "device": partition.device,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "percent": round(usage.percent, 1)
                    }
                except Exception as e:
                    self.logger.debug(f"Error getting disk info for {partition.mountpoint}: {e}")
            
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
                        "time_left": battery.secsleft if hasattr(battery, 'secsleft') and battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    }
            except Exception as e:
                self.logger.debug(f"Could not get battery info: {e}")
            
            # Windows-specific metrics via WMI
            wmi_metrics = self._get_wmi_metrics()
            
            metrics = {
                "windows_version": platform.win32_ver()[0],
                "windows_build": platform.win32_ver()[1],
                "edition": self._get_windows_edition(),
                
                "cpu": {
                    "percent": round(cpu_percent, 1),
                    "per_core": [round(p, 1) for p in cpu_per_core],
                    "cores": psutil.cpu_count(),
                    "cores_logical": psutil.cpu_count(logical=True)
                },
                
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 1),
                    "used_gb": round(memory.used / (1024**3), 1),
                    "available_gb": round(memory.available / (1024**3), 1),
                    "percent": round(memory.percent, 1)
                },
                
                "disks": disk_info,
                
                "network": {
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 1),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 1),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "active_connections": net_connections
                },
                
                "battery": battery_info,
                "wmi_metrics": wmi_metrics,
                "users": self._get_logged_in_users(),
                "uptime_seconds": time.time() - psutil.boot_time(),
                "system_boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
            self.logger.debug("Collected comprehensive Windows system metrics")
            return metrics
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def _get_wmi_metrics(self) -> Dict[str, Any]:
        """Get Windows-specific metrics via WMI"""
        if not self.wmi_conn:
            return {}
            
        try:
            wmi_info = {}
            
            # Temperature information
            try:
                temperatures = self.wmi_conn.Win32_TemperatureProbe()
                if temperatures:
                    wmi_info['temperatures'] = [
                        {
                            'name': temp.Name,
                            'reading': temp.CurrentReading,
                            'units': temp.Units
                        } for temp in temperatures
                    ]
            except:
                pass
            
            # Fan information
            try:
                fans = self.wmi_conn.Win32_Fan()
                if fans:
                    wmi_info['fans'] = [
                        {
                            'name': fan.Name,
                            'speed': fan.DesiredSpeed
                        } for fan in fans
                    ]
            except:
                pass
            
            # BIOS information
            try:
                bios = self.wmi_conn.Win32_BIOS()[0]
                wmi_info['bios'] = {
                    'manufacturer': bios.Manufacturer,
                    'version': bios.Version,
                    'release_date': bios.ReleaseDate
                }
            except:
                pass
            
            # Computer system information
            try:
                computer_system = self.wmi_conn.Win32_ComputerSystem()[0]
                wmi_info['computer_system'] = {
                    'manufacturer': computer_system.Manufacturer,
                    'model': computer_system.Model,
                    'total_physical_memory': int(computer_system.TotalPhysicalMemory) if computer_system.TotalPhysicalMemory else 0
                }
            except:
                pass
            
            return wmi_info
        except Exception as e:
            self.logger.debug(f"Error getting WMI metrics: {e}")
            return {}
    
    def _get_windows_edition(self) -> str:
        """Get Windows edition information"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                try:
                    edition = winreg.QueryValueEx(key, "EditionID")[0]
                    return edition
                except:
                    return "Unknown"
        except:
            return "Unknown"
    
    def _get_logged_in_users(self) -> List[Dict[str, Any]]:
        """Get information about logged-in users"""
        users = []
        try:
            for user in psutil.users():
                users.append({
                    "name": user.name,
                    "terminal": user.terminal or "Console",
                    "host": user.host,
                    "started": datetime.fromtimestamp(user.started).isoformat()
                })
        except Exception as e:
            self.logger.debug(f"Error getting user info: {e}")
        
        return users
    
    def get_event_logs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get Windows Event Logs"""
        if not HAS_WIN32:
            return {}
            
        event_logs = {
            "application": [],
            "system": [],
            "security": []
        }
        
        log_types = ['Application', 'System', 'Security']
        
        for log_type in log_types:
            try:
                hand = win32evtlog.OpenEventLog(None, log_type)
                total = win32evtlog.GetNumberOfEventLogRecords(hand)
                
                # Read recent events
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                
                event_count = 0
                for event in events:
                    if event_count >= 10:  # Limit per log type
                        break
                    
                    event_info = {
                        "event_id": event.EventID,
                        "source": event.SourceName,
                        "time_generated": event.TimeGenerated.isoformat(),
                        "message": self._clean_event_message(event.StringInserts),
                        "level": self._get_event_level(event.EventType)
                    }
                    
                    event_logs[log_type.lower()].append(event_info)
                    event_count += 1
                
                win32evtlog.CloseEventLog(hand)
            except Exception as e:
                self.logger.debug(f"Error reading {log_type} event log: {e}")
        
        return event_logs
    
    def _clean_event_message(self, message_inserts):
        """Clean event message inserts"""
        if message_inserts:
            return ' '.join(str(msg) for msg in message_inserts if msg)
        return ""
    
    def _get_event_level(self, event_type):
        """Convert event type to string level"""
        levels = {
            1: "ERROR",
            2: "WARNING", 
            4: "INFORMATION",
            8: "AUDIT_SUCCESS",
            16: "AUDIT_FAILURE"
        }
        return levels.get(event_type, "UNKNOWN")
    
    def get_additional_data(self) -> Dict[str, Any]:
        """Get additional Windows-specific data"""
        return {
            "browser_usage": self.get_browser_usage(),
            "application_usage": self.application_usage,
            "event_logs": self.get_event_logs(),
            "windows_updates": self._get_windows_update_info(),
            "installed_software": self._get_installed_software(),
            "network_shares": self._get_network_shares()
        }
    
    def _get_windows_update_info(self) -> Dict[str, Any]:
        """Get Windows Update information"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\Results") as key:
                try:
                    last_success = winreg.QueryValueEx(key, "LastSuccessTime")[0]
                    return {
                        "last_successful_update": last_success,
                        "update_service_running": self._is_service_running("wuauserv")
                    }
                except:
                    return {"update_service_running": self._is_service_running("wuauserv")}
        except:
            return {"update_service_running": False}
    
    def _is_service_running(self, service_name: str) -> bool:
        """Check if a Windows service is running"""
        try:
            result = subprocess.run(
                ['sc', 'query', service_name], 
                capture_output=True, text=True, timeout=5
            )
            return "RUNNING" in result.stdout
        except:
            return False
    
    def _get_installed_software(self) -> List[Dict[str, str]]:
        """Get list of installed software"""
        software_list = []
        registry_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        for path in registry_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    try:
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                    except:
                                        version = "Unknown"
                                    
                                    software_list.append({
                                        "name": display_name,
                                        "version": version
                                    })
                                except:
                                    pass
                            i += 1
                        except WindowsError:
                            break
            except:
                pass
        
        return software_list[:20]  # Limit to 20 items
    
    def _get_network_shares(self) -> List[Dict[str, str]]:
        """Get network shares"""
        shares = []
        try:
            result = subprocess.run(['net', 'share'], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if line.strip() and not line.startswith('Share name') and not line.startswith('---'):
                    parts = line.split()
                    if len(parts) >= 2:
                        shares.append({
                            "name": parts[0],
                            "path": parts[1]
                        })
        except:
            pass
        
        return shares
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform-specific information"""
        platform_info = get_system_info()
        platform_info.update({
            "client_type": "windows_desktop",
            "windows_version": platform.win32_ver()[0],
            "windows_edition": self._get_windows_edition(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine()
        })
        return platform_info


class BrowserMonitor:
    """Monitor browser usage and history"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def get_browser_usage(self) -> Dict[str, Any]:
        """Get browser usage information for all installed browsers"""
        browser_data = {}
        
        # Chrome/Edge tracking
        chrome_data = self._get_chrome_usage()
        if chrome_data:
            browser_data['chrome'] = chrome_data
        
        # Firefox tracking
        firefox_data = self._get_firefox_usage()
        if firefox_data:
            browser_data['firefox'] = firefox_data
        
        # Internet Explorer/Edge Legacy
        ie_data = self._get_ie_usage()
        if ie_data:
            browser_data['internet_explorer'] = ie_data
        
        return browser_data
    
    def _get_chrome_usage(self) -> Optional[Dict[str, Any]]:
        """Get Chrome/Edge usage data"""
        try:
            browsers = [
                ('chrome', 'Google\\Chrome'),
                ('edge', 'Microsoft\\Edge'),
                ('brave', 'BraveSoftware\\Brave-Browser'),
                ('opera', 'Opera Software\\Opera Stable')
            ]
            
            browser_data = {}
            for browser_name, browser_path in browsers:
                profiles = self._get_chrome_profiles(browser_path)
                if profiles:
                    browser_data[browser_name] = {
                        'profiles': profiles,
                        'process_count': self._get_browser_process_count(browser_name)
                    }
            
            return browser_data
        except Exception as e:
            self.logger.debug(f"Error getting Chrome usage: {e}")
            return None
    
    def _get_chrome_profiles(self, browser_path: str) -> List[Dict[str, Any]]:
        """Get Chrome profile information"""
        profiles = []
        user_profile = os.environ.get('USERPROFILE', '')
        browser_dir = os.path.join(user_profile, 'AppData', 'Local', browser_path, 'User Data')
        
        if not os.path.exists(browser_dir):
            return profiles
        
        try:
            # Look for profile directories
            for item in os.listdir(browser_dir):
                profile_path = os.path.join(browser_dir, item)
                if os.path.isdir(profile_path) and (item.startswith('Profile') or item == 'Default'):
                    history_db = os.path.join(profile_path, 'History')
                    
                    if os.path.exists(history_db):
                        # Copy database to avoid locking
                        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
                        try:
                            shutil.copy2(history_db, temp_db.name)
                            
                            conn = sqlite3.connect(temp_db.name)
                            cursor = conn.cursor()
                            
                            try:
                                # Get recent history
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
                                self.logger.debug(f"Error reading browser history: {e}")
                            finally:
                                conn.close()
                            os.unlink(temp_db.name)
                        except:
                            if os.path.exists(temp_db.name):
                                os.unlink(temp_db.name)
        except Exception as e:
            self.logger.debug(f"Error processing browser profiles: {e}")
        
        return profiles
    
    def _get_firefox_usage(self) -> Optional[Dict[str, Any]]:
        """Get Firefox usage data"""
        try:
            user_profile = os.environ.get('USERPROFILE', '')
            firefox_dir = os.path.join(user_profile, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles')
            
            if not os.path.exists(firefox_dir):
                return None
            
            profiles = []
            for item in os.listdir(firefox_dir):
                profile_path = os.path.join(firefox_dir, item)
                if os.path.isdir(profile_path) and item.endswith('.default-release'):
                    places_db = os.path.join(profile_path, 'places.sqlite')
                    
                    if os.path.exists(places_db):
                        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
                        try:
                            shutil.copy2(places_db, temp_db.name)
                            
                            conn = sqlite3.connect(temp_db.name)
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
                            os.unlink(temp_db.name)
                        except:
                            if os.path.exists(temp_db.name):
                                os.unlink(temp_db.name)
            
            if profiles:
                return {
                    'profiles': profiles,
                    'process_count': self._get_browser_process_count('firefox')
                }
        except Exception as e:
            self.logger.debug(f"Error getting Firefox usage: {e}")
        
        return None
    
    def _get_ie_usage(self) -> Optional[Dict[str, Any]]:
        """Get Internet Explorer usage data"""
        try:
            # IE history is stored in the registry and index.dat files
            # This is a simplified version - full implementation would be more complex
            return {
                'process_count': self._get_browser_process_count('iexplore'),
                'note': 'Detailed history tracking requires additional implementation'
            }
        except Exception as e:
            self.logger.debug(f"Error getting IE usage: {e}")
            return None
    
    def _get_browser_process_count(self, browser_name: str) -> int:
        """Get number of running browser processes"""
        try:
            count = 0
            for proc in psutil.process_iter(['name']):
                try:
                    if browser_name.lower() in proc.info['name'].lower():
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return count
        except:
            return 0


def main():
    parser = argparse.ArgumentParser(description="Enhanced Sentinel Windows Desktop Client")
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
        client = WindowsDesktopClient(args.config)
        if args.verbose:
            client.logger.setLevel("DEBUG")
        client.run()
    except KeyboardInterrupt:
        print("\nStopping Enhanced Windows Desktop Client...")
    except Exception as e:
        print(f"Failed to start client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()