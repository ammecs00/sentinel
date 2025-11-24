#!/usr/bin/env python3
"""
Enhanced Sentinel Linux Server Client
Comprehensive system analytics, process monitoring, and log categorization
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
import glob
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import gzip
import bz2

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from base_client import BaseMonitorClient
from config_manager import ConfigManager
from utils import setup_logging, get_system_info

class LinuxServerClient(BaseMonitorClient):
    def __init__(self, config_path: str):
        super().__init__(config_path, "linux_server")
        self.logger = setup_logging("linux_server")
        self.log_patterns = self._initialize_log_patterns()
        
    def _initialize_log_patterns(self) -> Dict[str, List[str]]:
        """Initialize log patterns for categorization"""
        return {
            "authentication": [
                r"authentication failure",
                r"failed password",
                r"invalid user",
                r"authentication succeeded",
                r"accepted password",
                r"session opened",
                r"session closed"
            ],
            "system_errors": [
                r"error:",
                r"failed",
                r"critical",
                r"panic",
                r"oom",
                r"out of memory",
                r"kernel:.*error",
                r"segfault",
                r"exception"
            ],
            "security": [
                r"firewall",
                r"iptables",
                r"ufw",
                r"intrusion",
                r"attack",
                r"brute force",
                r"port scan",
                r"malware",
                r"virus"
            ],
            "network": [
                r"network",
                r"connection",
                r"port",
                r"tcp",
                r"udp",
                r"dns",
                r"dhcp",
                r"interface",
                r"ethernet"
            ],
            "application": [
                r"apache",
                r"nginx",
                r"mysql",
                r"postgres",
                r"docker",
                r"kube",
                r"php",
                r"python",
                r"node"
            ]
        }
    
    def get_active_window(self) -> Optional[str]:
        """No active window on server"""
        return None
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get comprehensive process information"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent', 'create_time', 'cmdline', 'status']):
                try:
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
                        "open_files": len(proc.open_files()) if hasattr(proc, 'open_files') else 0
                    }
                    
                    # Add process categorization
                    process_info['category'] = self._categorize_process(proc.info['name'], process_info['cmdline'])
                    
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError) as e:
                    self.logger.debug(f"Error accessing process: {e}")
                    continue
            
            # Limit number of processes to prevent huge payloads
            processes = processes[:100]
            self.logger.debug(f"Collected {len(processes)} server processes")
            return processes
        except Exception as e:
            self.logger.error(f"Error getting process list: {e}")
            return []
    
    def _categorize_process(self, name: str, cmdline: str) -> str:
        """Categorize process based on name and command line"""
        categories = {
            'system': ['systemd', 'init', 'kthreadd', 'rcu_sched', 'migration'],
            'network': ['sshd', 'nginx', 'apache', 'httpd', 'postfix', 'dovecot', 'bind', 'named'],
            'database': ['mysql', 'mariadb', 'postgres', 'mongod', 'redis'],
            'web': ['nginx', 'apache', 'httpd', 'php', 'node', 'python'],
            'container': ['docker', 'containerd', 'dockerd', 'kubelet', 'k3s'],
            'monitoring': ['prometheus', 'grafana', 'zabbix', 'nagios'],
            'storage': ['lvm', 'mdadm', 'ceph', 'gluster']
        }
        
        name_lower = name.lower()
        cmdline_lower = cmdline.lower()
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
            if any(keyword in cmdline_lower for keyword in keywords):
                return category
        
        return 'application'
    
    def get_system_logs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Collect and categorize system logs"""
        log_files = [
            '/var/log/syslog',
            '/var/log/messages',
            '/var/log/auth.log',
            '/var/log/secure',
            '/var/log/kern.log',
            '/var/log/dmesg'
        ]
        
        categorized_logs = {category: [] for category in self.log_patterns.keys()}
        categorized_logs['other'] = []
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
            
            try:
                logs = self._read_log_file(log_file, max_lines=50)
                for log_entry in logs:
                    category = self._categorize_log_entry(log_entry)
                    if len(categorized_logs[category]) < 20:  # Limit per category
                        categorized_logs[category].append({
                            'file': os.path.basename(log_file),
                            'entry': log_entry,
                            'timestamp': datetime.now().isoformat()
                        })
            except Exception as e:
                self.logger.debug(f"Error reading log file {log_file}: {e}")
        
        return categorized_logs
    
    def _read_log_file(self, file_path: str, max_lines: int = 100) -> List[str]:
        """Read log file, handling compressed files"""
        lines = []
        
        try:
            if file_path.endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-max_lines:]
            elif file_path.endswith('.bz2'):
                with bz2.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-max_lines:]
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-max_lines:]
        except Exception as e:
            self.logger.debug(f"Error reading {file_path}: {e}")
        
        return [line.strip() for line in lines if line.strip()]
    
    def _categorize_log_entry(self, log_entry: str) -> str:
        """Categorize log entry based on patterns"""
        for category, patterns in self.log_patterns.items():
            for pattern in patterns:
                if re.search(pattern, log_entry, re.IGNORECASE):
                    return category
        return 'other'
    
    def get_container_info(self) -> List[Dict[str, Any]]:
        """Get comprehensive Docker container information"""
        containers = []
        try:
            # Get container list
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.ID}}'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            name, image, status, ports, container_id = line.split('|', 4)
                            
                            # Get detailed container info
                            stats = self._get_container_stats(container_id)
                            
                            container_info = {
                                "name": name,
                                "image": image,
                                "status": status,
                                "ports": ports,
                                "id": container_id[:12],
                                "stats": stats
                            }
                            containers.append(container_info)
                        except ValueError:
                            continue
            
            self.logger.debug(f"Found {len(containers)} Docker containers")
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            self.logger.debug(f"Docker not available or command failed: {e}")
        
        return containers
    
    def _get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource usage statistics"""
        try:
            result = subprocess.run(
                ['docker', 'stats', container_id, '--no-stream', '--format', '{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}|{{.BlockIO}}'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                cpu, memory, network, block_io = result.stdout.strip().split('|')
                return {
                    "cpu_percent": cpu.strip(),
                    "memory_usage": memory.strip(),
                    "network_io": network.strip(),
                    "block_io": block_io.strip()
                }
        except:
            pass
        
        return {}
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive service status"""
        services = {}
        common_services = [
            'nginx', 'apache2', 'httpd', 'mysql', 'mariadb', 'postgresql', 
            'docker', 'ssh', 'sshd', 'redis', 'mongod', 'php-fpm', 'node'
        ]
        
        for service in common_services:
            try:
                # Check service status
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True, text=True, timeout=2
                )
                status = result.stdout.strip()
                
                # Get service details
                if status != 'unknown':
                    # Get memory usage of service
                    memory_usage = self._get_service_memory_usage(service)
                    
                    services[service] = {
                        "status": status,
                        "memory_usage_mb": memory_usage,
                        "enabled": self._is_service_enabled(service)
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                services[service] = {"status": "unknown"}
        
        self.logger.debug(f"Checked status of {len(services)} services")
        return services
    
    def _get_service_memory_usage(self, service: str) -> float:
        """Get memory usage of service processes"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', service],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                total_memory = 0
                for pid in pids:
                    if pid.strip():
                        try:
                            proc = psutil.Process(int(pid.strip()))
                            total_memory += proc.memory_info().rss
                        except:
                            continue
                return round(total_memory / (1024*1024), 1)
        except:
            pass
        return 0.0
    
    def _is_service_enabled(self, service: str) -> bool:
        """Check if service is enabled to start on boot"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-enabled', service],
                capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip() == 'enabled'
        except:
            return False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive server metrics"""
        try:
            # System load
            load_avg = os.getloadavg()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics - multiple partitions
            disk_info = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_io = psutil.disk_io_counters(perdisk=True).get(partition.device.replace('/dev/', ''), {})
                    
                    disk_info[partition.mountpoint] = {
                        "device": partition.device,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "percent": round(usage.percent, 1),
                        "read_mb": round(disk_io.read_bytes / (1024**2), 1) if disk_io else 0,
                        "write_mb": round(disk_io.write_bytes / (1024**2), 1) if disk_io else 0
                    }
                except Exception:
                    continue
            
            # Network metrics
            net_io = psutil.net_io_counters()
            net_connections = psutil.net_connections()
            
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
            
            # Uptime
            uptime = time.time() - psutil.boot_time()
            
            metrics = {
                "load_average": {
                    "1min": round(load_avg[0], 2),
                    "5min": round(load_avg[1], 2),
                    "15min": round(load_avg[2], 2)
                },
                "cpu": {
                    "percent": round(cpu_percent, 1),
                    "cores": cpu_count,
                    "load_per_core": [round(p, 1) for p in cpu_per_core],
                    "frequency_mhz": round(cpu_freq.current, 1) if cpu_freq else None
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
                "temperatures": temp_info,
                "system": {
                    "uptime_days": round(uptime / (24 * 3600), 1),
                    "uptime_seconds": uptime,
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                    "users": len(psutil.users())
                }
            }
            
            self.logger.debug("Collected comprehensive system metrics")
            return metrics
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_additional_data(self) -> Dict[str, Any]:
        """Get additional server-specific data"""
        return {
            "services": self.get_service_status(),
            "containers": self.get_container_info(),
            "system_logs": self.get_system_logs(),
            "security_scan": self._perform_security_scan(),
            "package_updates": self._check_package_updates()
        }
    
    def _perform_security_scan(self) -> Dict[str, Any]:
        """Perform basic security checks"""
        security_checks = {}
        
        # Check for failed login attempts
        try:
            result = subprocess.run(
                ['grep', 'Failed password', '/var/log/auth.log'],
                capture_output=True, text=True
            )
            failed_logins = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            security_checks['failed_logins'] = failed_logins
        except:
            security_checks['failed_logins'] = 0
        
        # Check SSH configuration
        try:
            result = subprocess.run(
                ['grep', '^PermitRootLogin', '/etc/ssh/sshd_config'],
                capture_output=True, text=True
            )
            security_checks['root_ssh'] = 'yes' in result.stdout.lower() if result.stdout else False
        except:
            security_checks['root_ssh'] = False
        
        # Check firewall status
        try:
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
            security_checks['firewall_active'] = 'active' in result.stdout.lower()
        except:
            security_checks['firewall_active'] = False
        
        return security_checks
    
    def _check_package_updates(self) -> Dict[str, Any]:
        """Check for available package updates"""
        update_info = {}
        
        # Ubuntu/Debian
        try:
            subprocess.run(['apt-get', 'update'], capture_output=True, timeout=30)
            result = subprocess.run(
                ['apt-get', 'upgrade', '--dry-run'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                security_updates = 0
                regular_updates = 0
                
                for line in result.stdout.split('\n'):
                    if 'upgraded,' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'upgraded,':
                                regular_updates = int(parts[i-1])
                                break
                    elif 'security' in line.lower():
                        security_updates += 1
                
                update_info['apt'] = {
                    "security_updates": security_updates,
                    "regular_updates": regular_updates,
                    "last_checked": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.debug(f"Error checking APT updates: {e}")
        
        return update_info
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform-specific information"""
        platform_info = get_system_info()
        platform_info.update({
            "client_type": "linux_server",
            "kernel_version": platform.release(),
            "virtualization": self._get_virtualization_info(),
            "hardware": self._get_hardware_info()
        })
        return platform_info
    
    def _get_virtualization_info(self) -> Dict[str, Any]:
        """Get virtualization information"""
        try:
            result = subprocess.run(
                ['systemd-detect-virt'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return {
                    "type": result.stdout.strip(),
                    "detected": True
                }
        except:
            pass
        
        return {"type": "bare metal", "detected": False}
    
    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information"""
        hardware_info = {}
        
        # CPU info
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = f.read()
                model_match = re.search(r'model name\s*:\s*(.+)', cpu_info)
                if model_match:
                    hardware_info['cpu_model'] = model_match.group(1).strip()
        except:
            pass
        
        # Memory info
        try:
            with open('/proc/meminfo', 'r') as f:
                mem_info = f.read()
                total_match = re.search(r'MemTotal:\s*(\d+)', mem_info)
                if total_match:
                    hardware_info['memory_total_kb'] = int(total_match.group(1))
        except:
            pass
        
        return hardware_info

def main():
    parser = argparse.ArgumentParser(description="Enhanced Sentinel Linux Server Client")
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
        client = LinuxServerClient(args.config)
        if args.verbose:
            client.logger.setLevel("DEBUG")
        client.run()
    except KeyboardInterrupt:
        print("\nStopping Enhanced Linux Server Client...")
    except Exception as e:
        print(f"Failed to start client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()