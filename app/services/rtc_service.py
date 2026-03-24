"""
File: app/services/rtc_service.py

═══════════════════════════════════════════════════════════════════════════
RTC (Real-Time Clock) SERVICE - DS3231 Integration
═══════════════════════════════════════════════════════════════════════════

Module Description:
    Service for interfacing with DS3231 Real-Time Clock module via I2C.
    Provides accurate timekeeping for air-gapped/offline systems.
    
    The DS3231 is a highly accurate I2C real-time clock (RTC) with an 
    integrated temperature-compensated crystal oscillator (TCXO) and crystal.
    It maintains accurate time even when the Raspberry Pi is powered off,
    using a coin cell battery (CR2032).
    
    WHY WE NEED RTC:
    - Operating theatre systems are air-gapped (no internet/NTP)
    - Raspberry Pi loses time when powered off
    - Accurate timestamps essential for medical records
    - HIPAA/GDPR compliance requires accurate time logging
    - Battery-backed RTC maintains time during power loss

HARDWARE SPECIFICATIONS:
    - Module: DS3231 RTC
    - Interface: I2C (SMBus)
    - I2C Address: 0x68 (default)
    - Accuracy: ±2ppm (±1 minute per year)
    - Battery: CR2032 (lasts 8-10 years)
    - Operating Voltage: 2.3V - 5.5V
    - Temperature Range: -40°C to +85°C

RASPBERRY PI I2C CONNECTIONS:
    DS3231 Pin  →  Raspberry Pi Pin
    ─────────────────────────────────
    VCC         →  Pin 1  (3.3V)
    GND         →  Pin 6  (Ground)
    SDA         →  Pin 3  (GPIO 2 - SDA)
    SCL         →  Pin 5  (GPIO 3 - SCL)

CROSS-PLATFORM SUPPORT:
    - Raspberry Pi (Linux): Uses real DS3231 hardware via I2C
    - Windows (Development): Fake mode - returns system time
    - Graceful degradation: Falls back to system time if RTC unavailable

USAGE EXAMPLE:
    >>> from app.services.rtc_service import RTCService
    >>> 
    >>> # Initialize RTC
    >>> rtc = RTCService()
    >>> 
    >>> # Check if RTC is available
    >>> if rtc.is_available():
    >>>     # Sync system time from RTC
    >>>     rtc.sync_system_time()
    >>>     print("System time synced from RTC")
    >>> else:
    >>>     print("RTC not available, using system time")
    >>> 
    >>> # Read time from RTC
    >>> current_time = rtc.read_time()
    >>> print(f"RTC Time: {current_time}")
    >>> 
    >>> # Set RTC time (if system time is correct)
    >>> from datetime import datetime
    >>> rtc.set_time(datetime.now())

RASPBERRY PI I2C SETUP:
    1. Enable I2C:
       sudo raspi-config
       → Interface Options → I2C → Enable
    
    2. Install I2C tools:
       sudo apt-get install i2c-tools python3-smbus
    
    3. Verify DS3231 detected:
       sudo i2cdetect -y 1
       (Should show '68' at address 0x68)
    
    4. Install Python library:
       pip install smbus2

DEPENDENCIES:
    - smbus2 (Linux only): I2C communication library
    - datetime: Standard library for time operations
    - subprocess: For system time sync (Linux only)
    - platform: For OS detection

ERROR HANDLING:
    - Hardware not found: Graceful fallback to system time
    - I2C communication errors: Logged and recovered
    - Permission errors: Detected and reported
    - Invalid time values: Validated before use

SECURITY NOTES:
    - System time sync requires sudo/root privileges
    - Use visudo to grant specific permissions if needed
    - RTC data not encrypted (physical security assumed)

Author: OT Video Dev Team
Date: February 16, 2026
Version: 1.0.0
"""

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

import platform
from datetime import datetime
from typing import Tuple, Optional

# Conditional imports based on platform
# Only import smbus2 on Linux (where DS3231 hardware exists)
if platform.system() == "Linux":
    try:
        import smbus2
        SMBUS_AVAILABLE = True
    except ImportError:
        SMBUS_AVAILABLE = False
        print("WARNING: smbus2 not installed. RTC functionality disabled.")
        print("Install with: pip install smbus2")
else:
    # Windows/Mac - no I2C hardware
    SMBUS_AVAILABLE = False

# Import subprocess for system time sync (Linux only)
if platform.system() == "Linux":
    import subprocess

# Import logger
from app.utils.logger import AppLogger

# Initialize logger
logger = AppLogger("RTCService")


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# DS3231 I2C Configuration
DS3231_ADDRESS = 0x68  # Default I2C address for DS3231
I2C_BUS = 1  # I2C bus number (1 for Raspberry Pi, 0 for older models)

# DS3231 Register Addresses (for reading/writing time)
REG_SECONDS = 0x00  # Seconds register (0-59)
REG_MINUTES = 0x01  # Minutes register (0-59)
REG_HOURS = 0x02    # Hours register (0-23 for 24h mode)
REG_DAY = 0x03      # Day of week (1-7)
REG_DATE = 0x04     # Date of month (1-31)
REG_MONTH = 0x05    # Month (1-12)
REG_YEAR = 0x06     # Year (0-99, represents 2000-2099)

# Validation Constants
MIN_VALID_YEAR = 2024  # Minimum valid year (project start)
MAX_VALID_YEAR = 2099  # Maximum year DS3231 can represent


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def bcd_to_decimal(bcd: int) -> int:
    """
    Convert BCD (Binary-Coded Decimal) to normal decimal.
    
    DS3231 stores time values in BCD format where each nibble (4 bits)
    represents a decimal digit. For example:
    - BCD 0x23 = decimal 23 (not 35)
    - BCD 0x59 = decimal 59 (not 89)
    
    Args:
        bcd (int): BCD value to convert (0x00 to 0x99)
    
    Returns:
        int: Decimal value
    
    Example:
        >>> bcd_to_decimal(0x23)
        23
        >>> bcd_to_decimal(0x59)
        59
    """
    return ((bcd >> 4) * 10) + (bcd & 0x0F)


def decimal_to_bcd(decimal: int) -> int:
    """
    Convert normal decimal to BCD (Binary-Coded Decimal).
    
    Inverse of bcd_to_decimal(). Converts a decimal number to BCD format
    for writing to DS3231 registers.
    
    Args:
        decimal (int): Decimal value to convert (0 to 99)
    
    Returns:
        int: BCD value
    
    Example:
        >>> decimal_to_bcd(23)
        0x23
        >>> decimal_to_bcd(59)
        0x59
    """
    return ((decimal // 10) << 4) | (decimal % 10)


# ═══════════════════════════════════════════════════════════════════════════
# RTC SERVICE CLASS
# ═══════════════════════════════════════════════════════════════════════════

class RTCService:
    """
    Real-Time Clock service for DS3231 module.
    
    Provides high-level interface for:
    - Reading time from RTC
    - Setting RTC time
    - Syncing system time from RTC
    - Checking RTC availability
    
    CROSS-PLATFORM BEHAVIOR:
    - Linux + Hardware: Uses real DS3231 via I2C
    - Linux + No Hardware: Falls back to system time
    - Windows/Mac: Always uses system time (development mode)
    
    THREAD SAFETY:
    - Not thread-safe (I2C operations are not thread-safe)
    - Use external locking if called from multiple threads
    
    PERFORMANCE:
    - I2C read: ~1ms per register
    - Full time read: ~7ms (7 registers)
    - Negligible impact on application performance
    
    Attributes:
        bus (smbus2.SMBus): I2C bus connection (Linux only)
        rtc_available (bool): True if DS3231 hardware detected
        is_fake_mode (bool): True if using system time (no hardware)
    
    Example:
        >>> rtc = RTCService()
        >>> if rtc.is_available():
        >>>     time = rtc.read_time()
        >>>     print(f"RTC says: {time}")
    """
    
    def __init__(self):
        """
        Initialize RTC service.
        
        INITIALIZATION SEQUENCE:
        1. Detect operating system
        2. On Linux: Try to open I2C bus
        3. On Linux: Try to communicate with DS3231
        4. Set availability flags accordingly
        5. Log initialization status
        
        FAILURE MODES:
        - I2C not enabled: rtc_available = False
        - smbus2 not installed: rtc_available = False
        - DS3231 not connected: rtc_available = False
        - Wrong I2C address: rtc_available = False
        - Permission denied: rtc_available = False
        
        All failures result in graceful fallback to system time.
        """
        self.bus = None
        self.rtc_available = False
        self.is_fake_mode = False
        
        # Check platform
        self.platform = platform.system()
        
        if self.platform == "Linux" and SMBUS_AVAILABLE:
            # Linux with smbus2 - try to initialize real RTC
            try:
                # Open I2C bus (usually bus 1 on Raspberry Pi)
                self.bus = smbus2.SMBus(I2C_BUS)
                
                # Test communication by reading seconds register
                # If this succeeds, DS3231 is present and responding
                self.bus.read_byte_data(DS3231_ADDRESS, REG_SECONDS)
                
                # Success - RTC is available
                self.rtc_available = True
                logger.info(f"DS3231 RTC initialized successfully at address 0x{DS3231_ADDRESS:02X}")
                logger.info(f"I2C bus: {I2C_BUS}")
                
            except FileNotFoundError:
                # I2C not enabled on Raspberry Pi
                logger.warning("I2C device not found. Enable I2C in raspi-config")
                logger.warning("Falling back to system time")
                self.is_fake_mode = True
                
            except PermissionError:
                # User doesn't have I2C permissions
                logger.warning("Permission denied for I2C device")
                logger.warning("Add user to 'i2c' group: sudo usermod -a -G i2c $USER")
                logger.warning("Falling back to system time")
                self.is_fake_mode = True
                
            except OSError as e:
                # DS3231 not responding (not connected or wrong address)
                logger.warning(f"DS3231 not found at address 0x{DS3231_ADDRESS:02X}: {e}")
                logger.warning("Check connections and verify address with: sudo i2cdetect -y 1")
                logger.warning("Falling back to system time")
                self.is_fake_mode = True
                
            except Exception as e:
                # Unexpected error
                logger.error(f"Unexpected error initializing RTC: {e}")
                logger.warning("Falling back to system time")
                self.is_fake_mode = True
        else:
            # Windows/Mac or smbus2 not available - use fake mode
            if self.platform != "Linux":
                logger.info(f"Running on {self.platform} - RTC hardware not available")
                logger.info("Using system time (development mode)")
            else:
                logger.warning("smbus2 not installed - RTC functionality disabled")
                logger.info("Install with: pip install smbus2")
            
            self.is_fake_mode = True
    
    def is_available(self) -> bool:
        """
        Check if RTC hardware is available and working.
        
        Returns:
            bool: True if DS3231 RTC is available, False if using system time
        
        Use this before performing RTC-specific operations.
        If False, the service automatically falls back to system time.
        
        Example:
            >>> rtc = RTCService()
            >>> if rtc.is_available():
            >>>     print("RTC hardware detected")
            >>> else:
            >>>     print("Using system time")
        """
        return self.rtc_available
    
    def read_time(self) -> datetime:
        """
        Read current time from RTC (or system time if unavailable).
        
        OPERATION:
        1. If RTC available: Read time from DS3231 registers
        2. If RTC unavailable: Return current system time
        3. Validate time values
        4. Convert BCD to decimal
        5. Create datetime object
        
        DS3231 REGISTER LAYOUT:
        - REG_SECONDS (0x00): Seconds in BCD (0-59)
        - REG_MINUTES (0x01): Minutes in BCD (0-59)
        - REG_HOURS   (0x02): Hours in BCD (0-23, 24h mode)
        - REG_DAY     (0x03): Day of week (1-7, not used)
        - REG_DATE    (0x04): Date of month in BCD (1-31)
        - REG_MONTH   (0x05): Month in BCD (1-12)
        - REG_YEAR    (0x06): Year in BCD (0-99, represents 2000-2099)
        
        Returns:
            datetime: Current time from RTC or system
        
        Raises:
            No exceptions raised - falls back to system time on error
        
        Example:
            >>> rtc = RTCService()
            >>> current_time = rtc.read_time()
            >>> print(f"Current time: {current_time}")
            Current time: 2026-02-16 14:30:45
        """
        if self.rtc_available and self.bus:
            try:
                # Read all time registers from DS3231 (7 bytes)
                # More efficient than reading one by one
                seconds_bcd = self.bus.read_byte_data(DS3231_ADDRESS, REG_SECONDS)
                minutes_bcd = self.bus.read_byte_data(DS3231_ADDRESS, REG_MINUTES)
                hours_bcd = self.bus.read_byte_data(DS3231_ADDRESS, REG_HOURS)
                # day_bcd = self.bus.read_byte_data(DS3231_ADDRESS, REG_DAY)  # Not used
                date_bcd = self.bus.read_byte_data(DS3231_ADDRESS, REG_DATE)
                month_bcd = self.bus.read_byte_data(DS3231_ADDRESS, REG_MONTH)
                year_bcd = self.bus.read_byte_data(DS3231_ADDRESS, REG_YEAR)
                
                # Convert BCD to decimal
                seconds = bcd_to_decimal(seconds_bcd & 0x7F)  # Mask bit 7 (reserved)
                minutes = bcd_to_decimal(minutes_bcd & 0x7F)  # Mask bit 7 (reserved)
                hours = bcd_to_decimal(hours_bcd & 0x3F)      # Mask bits 6-7 (12/24h mode)
                date = bcd_to_decimal(date_bcd & 0x3F)        # Mask bits 6-7 (reserved)
                month = bcd_to_decimal(month_bcd & 0x1F)      # Mask bits 5-7 (century/reserved)
                year = bcd_to_decimal(year_bcd) + 2000        # DS3231 stores 0-99 for 2000-2099
                
                # Validate time values
                if not self._validate_time(year, month, date, hours, minutes, seconds):
                    logger.warning("Invalid time read from RTC, using system time")
                    return datetime.now()
                
                # Create datetime object
                rtc_time = datetime(year, month, date, hours, minutes, seconds)
                
                logger.debug(f"Read time from RTC: {rtc_time}")
                return rtc_time
                
            except Exception as e:
                # Communication error with DS3231
                logger.error(f"Error reading time from RTC: {e}")
                logger.warning("Falling back to system time")
                return datetime.now()
        else:
            # RTC not available - return system time
            return datetime.now()
    
    def set_time(self, dt: datetime) -> Tuple[bool, Optional[str]]:
        """
        Set RTC time to specified datetime.
        
        USE CASES:
        - Initial RTC setup
        - Correcting RTC drift
        - Syncing RTC to accurate external source
        
        OPERATION:
        1. Validate input datetime
        2. Convert decimal to BCD
        3. Write to DS3231 registers
        4. Verify write succeeded
        
        IMPORTANT NOTES:
        - This does NOT change system time
        - Use sync_system_time() after this to sync system clock
        - RTC continues running even when Pi is off
        - Battery must be installed for RTC to retain time
        
        Args:
            dt (datetime): Time to set on RTC
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        
        Example:
            >>> rtc = RTCService()
            >>> from datetime import datetime
            >>> # Set RTC to current system time
            >>> success, error = rtc.set_time(datetime.now())
            >>> if success:
            >>>     print("RTC time set successfully")
            >>> else:
            >>>     print(f"Failed to set RTC: {error}")
        """
        if not self.rtc_available or not self.bus:
            return False, "RTC hardware not available"
        
        try:
            # Validate year range (DS3231 supports 2000-2099)
            if dt.year < 2000 or dt.year > 2099:
                return False, f"Year {dt.year} out of range (2000-2099)"
            
            # Convert datetime to BCD values
            seconds_bcd = decimal_to_bcd(dt.second)
            minutes_bcd = decimal_to_bcd(dt.minute)
            hours_bcd = decimal_to_bcd(dt.hour)  # 24-hour format
            date_bcd = decimal_to_bcd(dt.day)
            month_bcd = decimal_to_bcd(dt.month)
            year_bcd = decimal_to_bcd(dt.year - 2000)  # DS3231 stores year as 0-99
            
            # Calculate day of week (1 = Monday, 7 = Sunday)
            day_of_week = dt.isoweekday()
            
            # Write time to DS3231 registers
            self.bus.write_byte_data(DS3231_ADDRESS, REG_SECONDS, seconds_bcd)
            self.bus.write_byte_data(DS3231_ADDRESS, REG_MINUTES, minutes_bcd)
            self.bus.write_byte_data(DS3231_ADDRESS, REG_HOURS, hours_bcd)
            self.bus.write_byte_data(DS3231_ADDRESS, REG_DAY, day_of_week)
            self.bus.write_byte_data(DS3231_ADDRESS, REG_DATE, date_bcd)
            self.bus.write_byte_data(DS3231_ADDRESS, REG_MONTH, month_bcd)
            self.bus.write_byte_data(DS3231_ADDRESS, REG_YEAR, year_bcd)
            
            logger.info(f"RTC time set to: {dt}")
            return True, None
            
        except Exception as e:
            error_msg = f"Error setting RTC time: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def sync_system_time(self) -> Tuple[bool, Optional[str]]:
        """
        Sync system time from RTC.
        
        CRITICAL OPERATION:
        This is typically called once at system boot to set the correct
        system time from the battery-backed RTC. Essential for air-gapped
        systems without internet/NTP access.
        
        OPERATION:
        1. Read time from DS3231
        2. Format time string for system
        3. Execute 'date' command with sudo
        4. Verify system time changed
        
        REQUIREMENTS:
        - Linux only (uses 'date' command)
        - Requires sudo/root privileges
        - RTC must be available
        
        PERMISSIONS:
        If you get permission errors, add to /etc/sudoers:
        username ALL=(ALL) NOPASSWD: /bin/date
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        
        Example:
            >>> rtc = RTCService()
            >>> if rtc.is_available():
            >>>     success, error = rtc.sync_system_time()
            >>>     if success:
            >>>         print("System time synced from RTC")
            >>>     else:
            >>>         print(f"Sync failed: {error}")
        """
        if not self.rtc_available:
            return False, "RTC hardware not available"
        
        if platform.system() != "Linux":
            return False, "System time sync only supported on Linux"
        
        try:
            # Read current time from RTC
            rtc_time = self.read_time()
            
            # Format time for 'date' command: "YYYY-MM-DD HH:MM:SS"
            time_string = rtc_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Set system time using 'date' command
            # Requires sudo privileges
            cmd = ["sudo", "date", "-s", time_string]
            
            logger.info(f"Syncing system time to: {time_string}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("System time successfully synced from RTC")
                return True, None
            else:
                error_msg = f"Failed to set system time: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "System time sync timed out"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Error syncing system time: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _validate_time(self, year: int, month: int, date: int, 
                       hours: int, minutes: int, seconds: int) -> bool:
        """
        Validate time values read from RTC.
        
        Checks if time values are within valid ranges and make sense.
        Prevents invalid times from corrupting the system.
        
        Args:
            year (int): Year (2000-2099)
            month (int): Month (1-12)
            date (int): Day of month (1-31)
            hours (int): Hours (0-23)
            minutes (int): Minutes (0-59)
            seconds (int): Seconds (0-59)
        
        Returns:
            bool: True if all values valid, False otherwise
        """
        # Check year range
        if year < MIN_VALID_YEAR or year > MAX_VALID_YEAR:
            logger.warning(f"Invalid year from RTC: {year}")
            return False
        
        # Check month range
        if month < 1 or month > 12:
            logger.warning(f"Invalid month from RTC: {month}")
            return False
        
        # Check date range (simplified - doesn't account for month lengths)
        if date < 1 or date > 31:
            logger.warning(f"Invalid date from RTC: {date}")
            return False
        
        # Check hours range
        if hours < 0 or hours > 23:
            logger.warning(f"Invalid hours from RTC: {hours}")
            return False
        
        # Check minutes range
        if minutes < 0 or minutes > 59:
            logger.warning(f"Invalid minutes from RTC: {minutes}")
            return False
        
        # Check seconds range
        if seconds < 0 or seconds > 59:
            logger.warning(f"Invalid seconds from RTC: {seconds}")
            return False
        
        # All checks passed
        return True
    
    def __del__(self):
        """
        Cleanup method called when RTCService object is destroyed.
        
        Properly closes I2C bus connection to avoid resource leaks.
        """
        if self.bus:
            try:
                self.bus.close()
                logger.debug("I2C bus closed")
            except:
                pass  # Ignore errors during cleanup


# ═══════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = ['RTCService']


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION (for testing)
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Test script for RTC service.
    
    Run this file directly to test RTC functionality:
        python3 app/services/rtc_service.py
    
    This will:
    1. Initialize RTC
    2. Read current time
    3. Display RTC status
    """
    print("=" * 60)
    print("DS3231 RTC Service Test")
    print("=" * 60)
    print()
    
    # Initialize RTC
    print("Initializing RTC...")
    rtc = RTCService()
    print()
    
    # Check availability
    if rtc.is_available():
        print("✓ DS3231 RTC detected and working")
        print()
        
        # Read time
        print("Reading time from RTC...")
        current_time = rtc.read_time()
        print(f"RTC Time: {current_time}")
        print(f"Formatted: {current_time.strftime('%A, %B %d, %Y at %I:%M:%S %p')}")
        print()
        
        # Compare with system time
        import datetime
        system_time = datetime.datetime.now()
        diff = abs((current_time - system_time).total_seconds())
        print(f"System Time: {system_time}")
        print(f"Time Difference: {diff:.2f} seconds")
        
        if diff > 5:
            print("⚠ WARNING: RTC and system time differ by more than 5 seconds")
            print("  Consider syncing system time from RTC or vice versa")
        else:
            print("✓ RTC and system time are in sync")
        
    else:
        print("✗ DS3231 RTC not available")
        if rtc.is_fake_mode:
            print("  Running in fake mode (using system time)")
        print()
        print("Troubleshooting steps:")
        print("1. Check DS3231 is connected to I2C pins")
        print("2. Enable I2C: sudo raspi-config → Interface Options → I2C")
        print("3. Install tools: sudo apt-get install i2c-tools")
        print("4. Check detection: sudo i2cdetect -y 1")
        print("5. Install smbus2: pip install smbus2")
    
    print()
    print("=" * 60)
