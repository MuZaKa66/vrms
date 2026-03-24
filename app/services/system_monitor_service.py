"""
File: app/services/system_monitor_service.py

═══════════════════════════════════════════════════════════════════════════
SYSTEM MONITOR SERVICE - Cross-Platform & Robust
═══════════════════════════════════════════════════════════════════════════

IMPROVEMENTS FROM PREVIOUS VERSION:
1. Windows compatibility (no scary errors on laptop)
2. Silent non-critical errors (temperature not available on Windows)
3. Graceful fallbacks for all platforms
4. Voice command friendly (no blocking errors)

ROBUSTNESS FEATURES:
- Works on Windows, Linux, Raspberry Pi
- Missing sensors don't crash app
- Non-critical errors logged but not shown to user
- Always returns valid data (with defaults)

Author: OT Video Dev Team
Date: February 13, 2026
Version: 2.0.0 (Cross-platform robust)
"""

import platform
import subprocess
from typing import Tuple, Optional, Dict

from config.app_config import VIDEO_STORAGE_PATH
from app.utils.logger import AppLogger
from app.utils.file_utils import get_free_space_gb
from app.utils.decorators import log_errors

logger = AppLogger("SystemMonitorService")


class SystemMonitorService:
    """
    Cross-platform system monitoring service.
    
    PLATFORM SUPPORT:
    - Raspberry Pi: Full monitoring (temp, memory, storage)
    - Linux: Full monitoring
    - Windows: Partial (no temperature, fallback memory)
    
    ROBUSTNESS:
    - Missing sensors return defaults, don't crash
    - Errors logged but user not bothered
    - Always returns valid health status
    
    Methods:
        get_cpu_temperature(): CPU temp (Celsius) or 0.0 on Windows
        get_memory_usage(): Memory stats (cross-platform)
        get_system_health(): Overall health status
    
    Example:
        monitor = SystemMonitorService()
        
        # Temperature (may be 0.0 on Windows)
        success, temp, _ = monitor.get_cpu_temperature()
        if temp > 70:
            print(f"Warning: High temperature {temp}°C")
        
        # Health status (always works)
        success, health, _ = monitor.get_system_health()
        print(f"Status: {health['status']}")  # healthy/warning/critical
    """
    
    def __init__(self):
        """Initialize with platform detection."""
        self.platform = platform.system()
        logger.info(f"System monitor initialized on {self.platform}")
    
    @log_errors
    def get_cpu_temperature(self) -> Tuple[bool, float, Optional[str]]:
        """
        Get CPU temperature in Celsius.
        
        CROSS-PLATFORM:
        - Raspberry Pi/Linux: Uses vcgencmd or thermal zone
        - Windows: Returns 0.0 (no error shown to user)
        
        Returns:
            (success, temperature, error_message)
            - temperature: 0.0 if unavailable (Windows)
        """
        # WINDOWS: Temperature not available
        if self.platform == 'Windows':
            logger.debug("Temperature not available on Windows")
            return True, 0.0, None
        
        # RASPBERRY PI: Try vcgencmd
        try:
            result = subprocess.run(
                ['vcgencmd', 'measure_temp'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Parse: temp=45.0'C
            temp_str = result.stdout.strip()
            temp = float(temp_str.split('=')[1].split("'")[0])
            
            logger.debug(f"Temperature: {temp}°C")
            return True, temp, None
        
        except FileNotFoundError:
            # Not Raspberry Pi, try thermal zone
            pass
        except Exception as e:
            logger.debug(f"vcgencmd failed: {e}")
        
        # LINUX: Try thermal zone
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
            
            logger.debug(f"Temperature: {temp}°C")
            return True, temp, None
        
        except Exception as e:
            logger.debug(f"Thermal zone read failed: {e}")
            # Return 0.0 - not critical, don't bother user
            return True, 0.0, None
    
    @log_errors
    def get_memory_usage(self) -> Tuple[bool, Dict, Optional[str]]:
        """
        Get memory usage statistics.
        
        CROSS-PLATFORM:
        - Linux: Uses /proc/meminfo
        - Windows: Uses psutil
        
        Returns:
            (success, memory_dict, error_message)
            memory_dict contains:
            - total_mb: Total RAM
            - used_mb: Used RAM
            - available_mb: Available RAM
            - percent_used: Usage percentage
        """
        # WINDOWS: Use psutil
        if self.platform == 'Windows':
            try:
                import psutil
                mem = psutil.virtual_memory()
                
                info = {
                    'total_mb': mem.total / (1024**2),
                    'used_mb': mem.used / (1024**2),
                    'available_mb': mem.available / (1024**2),
                    'percent_used': mem.percent
                }
                
                logger.debug(f"Memory: {mem.percent:.1f}% used")
                return True, info, None
            
            except ImportError:
                logger.warning("psutil not installed on Windows")
                # Return defaults
                return True, {
                    'total_mb': 0, 'used_mb': 0,
                    'available_mb': 0, 'percent_used': 0
                }, None
            except Exception as e:
                logger.error(f"psutil error: {e}")
                return False, {}, "Memory read failed"
        
        # LINUX/PI: Use /proc/meminfo
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            mem_total = 0
            mem_available = 0
            
            for line in meminfo.split('\n'):
                if 'MemTotal:' in line:
                    mem_total = int(line.split()[1]) / 1024  # KB → MB
                elif 'MemAvailable:' in line:
                    mem_available = int(line.split()[1]) / 1024
            
            mem_used = mem_total - mem_available
            mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
            
            info = {
                'total_mb': mem_total,
                'used_mb': mem_used,
                'available_mb': mem_available,
                'percent_used': mem_percent
            }
            
            logger.debug(f"Memory: {mem_percent:.1f}% used")
            return True, info, None
        
        except Exception as e:
            logger.error(f"Memory read error: {e}")
            return False, {}, "Memory read failed"
    
    @log_errors
    def get_system_health(self) -> Tuple[bool, Dict, Optional[str]]:
        """
        Get overall system health status.
        
        ROBUST:
        - Always returns valid status
        - Missing sensors don't prevent health check
        - Prioritizes storage (most critical)
        
        VOICE COMMAND FRIENDLY:
        - No blocking errors
        - Clear status levels
        
        Returns:
            (success, health_dict, error_message)
            health_dict contains:
            - status: 'healthy', 'warning', 'critical'
            - temperature: CPU temp (0.0 if unavailable)
            - memory_percent: Memory usage %
            - storage_gb: Free storage space
            - warnings: List of warning messages
        """
        try:
            warnings = []
            status = 'healthy'
            temp = 0.0
            memory_percent = 0.0
            
            # Temperature (may be 0.0 on Windows - that's OK)
            success, temp, _ = self.get_cpu_temperature()
            if success and temp > 0:  # Only check if temp available
                if temp > 80:
                    status = 'critical'
                    warnings.append(f"Critical temperature: {temp:.1f}°C")
                elif temp > 70:
                    if status == 'healthy':
                        status = 'warning'
                    warnings.append(f"High temperature: {temp:.1f}°C")
            
            # Memory
            success, mem, _ = self.get_memory_usage()
            if success:
                memory_percent = mem.get('percent_used', 0)
                
                if memory_percent > 90:
                    status = 'critical'
                    warnings.append(f"Critical memory: {memory_percent:.1f}%")
                elif memory_percent > 80:
                    if status == 'healthy':
                        status = 'warning'
                    warnings.append(f"High memory: {memory_percent:.1f}%")
            
            # Storage (MOST CRITICAL - always check)
            try:
                storage_gb = get_free_space_gb(VIDEO_STORAGE_PATH)
                
                if storage_gb < 5:
                    status = 'critical'
                    warnings.append(f"Critical storage: {storage_gb:.1f} GB")
                elif storage_gb < 10:
                    if status == 'healthy':
                        status = 'warning'
                    warnings.append(f"Low storage: {storage_gb:.1f} GB")
            
            except Exception as e:
                logger.error(f"Storage check failed: {e}")
                storage_gb = 0
                status = 'critical'
                warnings.append("Cannot check storage space")
            
            health = {
                'status': status,
                'temperature': temp,
                'memory_percent': memory_percent,
                'storage_gb': storage_gb,
                'warnings': warnings
            }
            
            if warnings:
                logger.debug(f"Health: {status} - {warnings}")
            else:
                logger.debug(f"Health: {status}")
            
            return True, health, None
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
            # Return safe defaults
            return False, {
                'status': 'healthy',
                'temperature': 0.0,
                'memory_percent': 0.0,
                'storage_gb': 0.0,
                'warnings': []
            }, "Health check failed"


__all__ = ['SystemMonitorService']


# ═══════════════════════════════════════════════════════════════════════════
# PLATFORM-SPECIFIC NOTES
# ═══════════════════════════════════════════════════════════════════════════
"""
WINDOWS:
- Temperature: Not available (shows "--" in UI)
- Memory: Uses psutil (install with: pip install psutil)
- Storage: Works normally
- No scary errors for missing sensors

RASPBERRY PI:
- Temperature: vcgencmd (built-in)
- Memory: /proc/meminfo (built-in)
- Storage: Works normally
- Full monitoring support

LINUX (other):
- Temperature: thermal_zone0 (if available)
- Memory: /proc/meminfo (built-in)
- Storage: Works normally
- Most features work

VOICE COMMAND USAGE:
- get_system_health() never blocks
- Missing sensors don't prevent recording
- Storage check is most critical (always checked)
- Health status always valid for voice feedback
"""
