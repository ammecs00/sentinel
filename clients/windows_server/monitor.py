#!/usr/bin/env python3
"""
Enhanced Sentinel Windows Server Client
Comprehensive system analytics, process monitoring, and log categorization for Windows Server
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
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import threading

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from base_client import BaseMonitorClient
from config_manager import ConfigManager
from utils import setup_logging, get_system_info

try:
    import win32evtlog
    import win32service
    import win32security
    import pythoncom
    import wmi
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("Warning: pywin32 not available. Some advanced features disabled.")

class WindowsServerClient(BaseMonitorClient):
    def __init__(self, config_path: str):
        super().__init__(config_path, "windows_server")
        self.logger = setup_logging("windows_server")
        self.log_patterns = self._initialize_log_patterns()
        
        # Initialize WMI for advanced system monitoring
        self.wmi_conn = None
        if HAS_WIN32:
            try:
                pythoncom.CoInitialize()
                self.wmi_conn = wmi.WMI()
            except Exception as e:
                self.logger.warning(f"Failed to initialize WMI: {e}")
    
    def _initialize_log_patterns(self) -> Dict[str, List[str]]:
        """Initialize log patterns for categorization"""
        return {
            "authentication": [
                r"logon",
                r"logoff",
                r"authentication",
                r"credential",
                r"password",
                r"user.*success",
                r"user.*fail"
            ],
            "security": [
                r"audit",
                r"security",
                r"firewall",
                r" intrusion",
                r"attack",
                r"malware",
                r"virus",
                r"threat",
                r"breach"
            ],
            "system_errors": [
                r"error",
                r"failed",
                r"critical",
                r"failure",
                r"timeout",
                r"crash",
                r"hang",
                r"unexpected"
            ],
            "application": [
                r"application",
                r"service",
                r"iis",
                r"sql",
                r"database",
                r"web",
                r"http",
                r"https"
            ],
            "network": [
                r"network",
                r"connection",
                r"tcp",
                r"udp",
                r"port",
                r"dns",
                r"dhcp",
                r"ip address"
            ]
        }
    
    def get_active_window(self) -> Optional[str]:
        """No active window on server"""
        return None
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get comprehensive process information for server applications"""
        server_keywords = [
            'sql', 'mysql', 'postgres', 'mongod', 'redis', 'apache', 'httpd',
            'nginx', 'iis', 'w3wp', 'tomcat', 'java', 'node', 'python', 'ruby',
            'powershell', 'cmd', 'services', 'svchost', 'lsass', 'winlogon',
            'spoolsv', 'taskhost', 'searchindexer', 'system', 'idle'
        ]
        
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent', 'create_time', 'cmdline', 'status']):
                try:
                    proc_name = proc.info['name'].lower().replace('.exe', '')
                    
                    # Include system processes and server applications
                    is_system_process = 'SYSTEM' in proc.info['username'] or 'NETWORK SERVICE' in proc.info['username']
                    is_server_process = any(keyword in proc_name for keyword in server_keywords)
                    
                    if is_system_process or is_server_process:
                        process_info = {
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "user": proc.info['username'],
                            "memory_rss_mb": round(proc.info['memory_info'].rss / (1024*1024), 1) if proc.info['memory_info'] else 0,
                            "memory_vms_mb": round(proc.info['memory_info'].vms / (1024*1024), 1) if proc.info['memory_info'] else 0,
                            "cpu_percent": round(proc.info['cpu_percent'] or 0, 1),
                            "status": proc.info['status'],
                            "create_time": datetime.fromtimestamp(proc.info['create_time']).isoformat() if proc.info['create_time'] else None,
                            "cmdline": ' '.join(proc.info['cmdline'] or [])[:500] if proc.info['cmdline'] else '',
                            "threads": proc.num_threads(),
                            "category": self._categorize_process(proc.info['name'], proc.info['cmdline'] or [])
                        }
                        processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError) as e:
                    self.logger.debug(f"Error accessing process: {e}")
                    continue
            
            # Limit number of processes
            processes = processes[:100]
            self.logger.debug(f"Collected {len(processes)} server processes")
            return processes
        except Exception as e:
            self.logger.error(f"Error getting process list: {e}")
            return []
    
    def _categorize_process(self, name: str, cmdline: List[str]) -> str:
        """Categorize process based on name and command line"""
        categories = {
            'system': ['system', 'svchost', 'lsass', 'winlogon', 'services', 'csrss', 'smss'],
            'network': ['iis', 'w3wp', 'httpd', 'nginx', 'apache', 'tomcat', 'node', 'python'],
            'database': ['sql', 'mysql', 'postgres', 'mongod', 'redis', 'oracle'],
            'web': ['iis', 'w3wp', 'nginx', 'apache', 'tomcat', 'httpd'],
            'security': ['defender', 'security', 'antivirus', 'firewall'],
            'storage': ['sql', 'mysql', 'postgres', 'mongod'],
            'monitoring': ['zabbix', 'nagios', 'prometheus', 'grafana']
        }
        
        name_lower = name.lower()
        cmdline_str = ' '.join(cmdline).lower()
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
            if any(keyword in cmdline_str for keyword in keywords):
                return category
        
        return 'application'
    
    def get_event_logs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get and categorize Windows Event Logs"""
        if not HAS_WIN32:
            return {}
            
        log_categories = {
            "application": [],
            "system": [],
            "security": [],
            "directory service": [],
            "dns server": [],
            "file replication service": []
        }
        
        for log_name in log_categories.keys():
            try:
                hand = win32evtlog.OpenEventLog(None, log_name)
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                
                event_count = 0
                for event in events:
                    if event_count >= 15:  # Limit per log
                        break
                    
                    event_message = self._clean_event_message(event.StringInserts)
                    category = self._categorize_log_entry(event_message, event.SourceName)
                    
                    event_info = {
                        "event_id": event.EventID,
                        "source": event.SourceName,
                        "time_generated": event.TimeGenerated.isoformat(),
                        "message": event_message,
                        "level": self._get_event_level(event.EventType),
                        "category": category
                    }
                    
                    log_categories[log_name].append(event_info)
                    event_count += 1
                
                win32evtlog.CloseEventLog(hand)
            except Exception as e:
                self.logger.debug(f"Error reading {log_name} event log: {e}")
        
        return log_categories
    
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
    
    def _categorize_log_entry(self, message: str, source: str) -> str:
        """Categorize log entry based on patterns and source"""
        message_lower = message.lower()
        source_lower = source.lower()
        
        for category, patterns in self.log_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return category
                if re.search(pattern, source_lower, re.IGNORECASE):
                    return category
        
        return 'other'
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive Windows service status"""
        services = {}
        
        common_services = [
            'MSSQLSERVER', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
            'W3SVC', 'IISADMIN', 'Tomcat', 'Apache', 'nginx', 'Spooler',
            'EventLog', 'Schedule', 'Server', 'Workstation', 'BFE',
            'WinDefend', 'Dnscache', 'Dhcp', 'LanmanServer', 'LanmanWorkstation'
        ]
        
        for service in common_services:
            try:
                # Use WMI for detailed service information
                if self.wmi_conn:
                    wmi_services = self.wmi_conn.Win32_Service(Name=service)
                    if wmi_services:
                        wmi_service = wmi_services[0]
                        services[service] = {
                            "status": wmi_service.State,
                            "start_mode": wmi_service.StartMode,
                            "start_name": wmi_service.StartName,
                            "path": wmi_service.PathName,
                            "process_id": wmi_service.ProcessId
                        }
                        continue
                
                # Fallback to SC command
                result = subprocess.run(
                    ['sc', 'query', service],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    status = "UNKNOWN"
                    for line in lines:
                        if 'STATE' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                status = parts[1].strip().split(' ')[0]
                                break
                    
                    services[service] = {
                        "status": status,
                        "process_id": self._get_service_process_id(service)
                    }
                else:
                    services[service] = {"status": "NOT_FOUND"}
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                services[service] = {"status": "UNKNOWN"}
        
        self.logger.debug(f"Checked status of {len(services)} services")
        return services
    
    def _get_service_process_id(self, service_name: str) -> Optional[int]:
        """Get process ID for a service"""
        try:
            if self.wmi_conn:
                wmi_services = self.wmi_conn.Win32_Service(Name=service_name)
                if wmi_services:
                    return wmi_services[0].ProcessId
        except:
            pass
        return None
    
    def get_iis_status(self) -> Dict[str, Any]:
        """Get IIS server status and sites"""
        iis_info = {}
        
        try:
            # Check if IIS is installed
            result = subprocess.run(
                ['Get-WindowsFeature', 'Web-Server'],
                capture_output=True, text=True, shell=True, timeout=10
            )
            if 'Installed' in result.stdout:
                iis_info['installed'] = True
                
                # Get IIS sites (simplified - would use IIS module in production)
                try:
                    result = subprocess.run(
                        ['Import-Module', 'WebAdministration'; 'Get-IISSite'],
                        capture_output=True, text=True, shell=True, timeout=10
                    )
                    iis_info['sites'] = []
                    
                    # Parse sites from output (simplified)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Name' in line and 'State' in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                iis_info['sites'].append({
                                    'name': parts[0],
                                    'state': parts[1]
                                })
                except:
                    iis_info['sites'] = []
            else:
                iis_info['installed'] = False
        except:
            iis_info['installed'] = False
        
        return iis_info
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive Windows server metrics"""
        try:
            # System load (Windows doesn't have load average like Linux)
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics - multiple drives
            disk_info = {}
            for partition in psutil.disk_partitions():
                try:
                    if 'cdrom' in partition.opts:
                        continue
                    usage = psutil.disk_usage(partition.mountpoint)
                    
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
            net_connections = psutil.net_connections()
            
            # WMI metrics for server-specific information
            wmi_metrics = self._get_wmi_server_metrics()
            
            metrics = {
                "windows_version": platform.win32_ver()[0],
                "windows_edition": self._get_windows_edition(),
                "server_role": self._get_server_role(),
                
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
                    "percent": round(memory.percent, 1),
                    "swap_used_gb": round(swap.used / (1024**3), 1),
                    "swap_total_gb": round(swap.total / (1024**3), 1),
                    "swap_percent": round(swap.percent, 1) if swap.total > 0 else 0
                },
                
                "disks": disk_info,
                
                "network": {
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 1),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 1),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "active_connections": len(net_connections),
                    "tcp_connections": len([c for c in net_connections if c.type == 1]),
                    "udp_connections": len([c for c in net_connections if c.type == 2])
                },
                
                "wmi_metrics": wmi_metrics,
                "system": {
                    "uptime_seconds": time.time() - psutil.boot_time(),
                    "uptime_days": round((time.time() - psutil.boot_time()) / (24 * 3600), 1),
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                    "users": len(psutil.users())
                }
            }
            
            self.logger.debug("Collected comprehensive Windows server metrics")
            return metrics
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def _get_wmi_server_metrics(self) -> Dict[str, Any]:
        """Get Windows Server-specific metrics via WMI"""
        if not self.wmi_conn:
            return {}
            
        try:
            wmi_info = {}
            
            # Server features
            try:
                features = self.wmi_conn.Win32_ServerFeature()
                if features:
                    wmi_info['server_features'] = [feature.Name for feature in features]
            except:
                pass
            
            # Page file information
            try:
                page_files = self.wmi_conn.Win32_PageFileUsage()
                if page_files:
                    wmi_info['page_files'] = [
                        {
                            'name': pf.Name,
                            'allocated_gb': round(int(pf.AllocatedBaseSize) / 1024, 1),
                            'current_usage_gb': round(int(pf.CurrentUsage) / 1024, 1)
                        } for pf in page_files
                    ]
            except:
                pass
            
            # Logical disks with detailed info
            try:
                logical_disks = self.wmi_conn.Win32_LogicalDisk()
                if logical_disks:
                    wmi_info['logical_disks'] = [
                        {
                            'device_id': ld.DeviceID,
                            'size_gb': round(int(ld.Size) / (1024**3), 1) if ld.Size else 0,
                            'free_space_gb': round(int(ld.FreeSpace) / (1024**3), 1) if ld.FreeSpace else 0,
                            'file_system': ld.FileSystem
                        } for ld in logical_disks if ld.Size
                    ]
            except:
                pass
            
            # Network adapters
            try:
                adapters = self.wmi_conn.Win32_NetworkAdapter(NetEnabled=True)
                if adapters:
                    wmi_info['network_adapters'] = [
                        {
                            'name': adapter.Name,
                            'mac_address': adapter.MACAddress,
                            'speed_mbps': int(adapter.Speed) // 1000000 if adapter.Speed else 0
                        } for adapter in adapters
                    ]
            except:
                pass
            
            return wmi_info
        except Exception as e:
            self.logger.debug(f"Error getting WMI server metrics: {e}")
            return {}
    
    def _get_windows_edition(self) -> str:
        """Get Windows Server edition information"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                try:
                    edition = winreg.QueryValueEx(key, "EditionID")[0]
                    return edition
                except:
                    product_name = winreg.QueryValueEx(key, "ProductName")[0]
                    return product_name
        except:
            return "Unknown"
    
    def _get_server_role(self) -> str:
        """Get Windows Server role information"""
        try:
            # Check common server roles
            roles = []
            
            # Domain Controller
            try:
                result = subprocess.run(
                    ['dsquery', 'server'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    roles.append("Domain Controller")
            except:
                pass
            
            # DNS Server
            try:
                result = subprocess.run(
                    ['Get-WindowsFeature', 'DNS'],
                    capture_output=True, text=True, shell=True, timeout=5
                )
                if 'Installed' in result.stdout:
                    roles.append("DNS Server")
            except:
                pass
            
            # DHCP Server
            try:
                result = subprocess.run(
                    ['Get-WindowsFeature', 'DHCP'],
                    capture_output=True, text=True, shell=True, timeout=5
                )
                if 'Installed' in result.stdout:
                    roles.append("DHCP Server")
            except:
                pass
            
            # Web Server (IIS)
            try:
                result = subprocess.run(
                    ['Get-WindowsFeature', 'Web-Server'],
                    capture_output=True, text=True, shell=True, timeout=5
                )
                if 'Installed' in result.stdout:
                    roles.append("Web Server")
            except:
                pass
            
            return ', '.join(roles) if roles else "Standalone Server"
        except:
            return "Unknown"
    
    def get_additional_data(self) -> Dict[str, Any]:
        """Get additional server-specific data"""
        return {
            "services": self.get_service_status(),
            "event_logs": self.get_event_logs(),
            "iis_status": self.get_iis_status(),
            "security_scan": self._perform_security_scan(),
            "windows_updates": self._get_windows_update_info(),
            "installed_roles": self._get_installed_roles()
        }
    
    def _perform_security_scan(self) -> Dict[str, Any]:
        """Perform basic security checks for Windows Server"""
        security_checks = {}
        
        # Check UAC status
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System") as key:
                try:
                    uac_value = winreg.QueryValueEx(key, "EnableLUA")[0]
                    security_checks['uac_enabled'] = uac_value == 1
                except:
                    security_checks['uac_enabled'] = False
        except:
            security_checks['uac_enabled'] = False
        
        # Check Windows Defender status
        try:
            result = subprocess.run(
                ['Get-MpComputerStatus'],
                capture_output=True, text=True, shell=True, timeout=5
            )
            security_checks['defender_enabled'] = 'True' in result.stdout
        except:
            security_checks['defender_enabled'] = False
        
        # Check firewall status
        try:
            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles'],
                capture_output=True, text=True, timeout=5
            )
            security_checks['firewall_enabled'] = 'ON' in result.stdout
        except:
            security_checks['firewall_enabled'] = False
        
        # Check for failed logins
        security_checks['failed_logins'] = self._count_failed_logins()
        
        return security_checks
    
    def _count_failed_logins(self) -> int:
        """Count failed login attempts from security log"""
        if not HAS_WIN32:
            return 0
            
        try:
            hand = win32evtlog.OpenEventLog(None, "Security")
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            
            failed_count = 0
            for event in events:
                if event.EventID in [4625, 4624]:  # Failed/Success logon
                    if event.EventID == 4625:  # Failed logon
                        failed_count += 1
                if failed_count >= 100:  # Limit check
                    break
            
            win32evtlog.CloseEventLog(hand)
            return failed_count
        except:
            return 0
    
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
    
    def _get_installed_roles(self) -> List[str]:
        """Get installed Windows Server roles"""
        roles = []
        try:
            result = subprocess.run(
                ['Get-WindowsFeature'],
                capture_output=True, text=True, shell=True, timeout=10
            )
            lines = result.stdout.split('\n')
            for line in lines:
                if '[X]' in line:
                    role = line.split('[X]')[-1].strip()
                    if role:
                        roles.append(role)
        except:
            pass
        
        return roles[:20]  # Limit to 20 roles
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform-specific information"""
        platform_info = get_system_info()
        platform_info.update({
            "client_type": "windows_server",
            "windows_version": platform.win32_ver()[0],
            "windows_edition": self._get_windows_edition(),
            "server_role": self._get_server_role(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine()
        })
        return platform_info


def main():
    parser = argparse.ArgumentParser(description="Enhanced Sentinel Windows Server Client")
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
        client = WindowsServerClient(args.config)
        if args.verbose:
            client.logger.setLevel("DEBUG")
        client.run()
    except KeyboardInterrupt:
        print("\nStopping Enhanced Windows Server Client...")
    except Exception as e:
        print(f"Failed to start client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()