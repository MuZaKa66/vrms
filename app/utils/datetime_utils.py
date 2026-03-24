
"""
File: app/utils/datetime_utils.py

Module Description:
    Date and time utilities for the OT Video Management System.
    
    Provides functions for:
    - Timestamp generation and formatting
    - Duration calculations and formatting
    - Date/time parsing
    - Human-readable time displays
    - Recording time tracking
    
    All timestamps use ISO 8601 format (YYYY-MM-DD HH:MM:SS) for consistency
    and database compatibility.

Dependencies:
    - datetime: Python standard library for date/time operations
    - time: For time-related operations

Usage Example:
    >>> from app.utils.datetime_utils import get_timestamp, format_duration
    >>> timestamp = get_timestamp()
    >>> print(timestamp)
    2026-01-28 14:30:22
    >>> 
    >>> duration_str = format_duration(3665)  # 1 hour, 1 minute, 5 seconds
    >>> print(duration_str)
    1:01:05

Author: OT Video Dev Team
Date: January 28, 2026
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
from datetime import datetime, timedelta, date
from typing import Optional, Tuple
import time

from app.utils.logger import AppLogger

#******
from datetime import datetime

def get_date():
    """Get current date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")

def get_time():
    """Get current time as HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")


def get_timestamp():
    """Get current timestamp."""
    return datetime.now().isoformat()


#********



# Initialize module logger
logger = AppLogger("DateTimeUtils")


# ============================================================================
# TIMESTAMP FUNCTIONS
# ============================================================================
def get_timestamp(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Get current timestamp as formatted string.
    
    Default format is ISO 8601: YYYY-MM-DD HH:MM:SS
    This format is sortable, unambiguous, and database-friendly.
    
    Args:
        fmt: strftime format string (default: ISO 8601)
    
    Returns:
        str: Formatted timestamp
    
    Example:
        >>> timestamp = get_timestamp()
        >>> print(timestamp)
        2026-01-28 14:30:22
        
        >>> # Custom format
        >>> timestamp = get_timestamp("%d/%m/%Y %I:%M %p")
        >>> print(timestamp)
        28/01/2026 02:30 PM
    """
    return datetime.now().strftime(fmt)


def get_date_string(fmt: str = "%Y-%m-%d") -> str:
    """
    Get current date as formatted string.
    
    Args:
        fmt: strftime format string (default: YYYY-MM-DD)
    
    Returns:
        str: Formatted date
    
    Example:
        >>> date_str = get_date_string()
        >>> print(date_str)
        2026-01-28
        
        >>> # Different format
        >>> date_str = get_date_string("%d %B %Y")
        >>> print(date_str)
        28 January 2026
    """
    return datetime.now().strftime(fmt)


def get_time_string(fmt: str = "%H:%M:%S") -> str:
    """
    Get current time as formatted string.
    
    Args:
        fmt: strftime format string (default: HH:MM:SS 24-hour)
    
    Returns:
        str: Formatted time
    
    Example:
        >>> time_str = get_time_string()
        >>> print(time_str)
        14:30:22
        
        >>> # 12-hour format
        >>> time_str = get_time_string("%I:%M:%S %p")
        >>> print(time_str)
        02:30:22 PM
    """
    return datetime.now().strftime(fmt)


def parse_timestamp(timestamp_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string to parse
        fmt: Expected format of the string
    
    Returns:
        datetime: Parsed datetime object, None if parsing fails
    
    Example:
        >>> dt = parse_timestamp("2026-01-28 14:30:22")
        >>> print(dt.year)
        2026
        
        >>> # Invalid timestamp returns None
        >>> dt = parse_timestamp("invalid")
        >>> print(dt)
        None
    """
    try:
        return datetime.strptime(timestamp_str, fmt)
    except ValueError as e:
        logger.error(f"Error parsing timestamp '{timestamp_str}': {e}")
        return None


# ============================================================================
# DURATION FUNCTIONS
# ============================================================================
def format_duration(seconds: int, show_hours: bool = True) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Formats as:
    - HH:MM:SS if hours > 0 or show_hours=True
    - MM:SS if hours = 0 and show_hours=False
    
    Args:
        seconds: Duration in seconds
        show_hours: Always show hours even if 0
    
    Returns:
        str: Formatted duration string
    
    Example:
        >>> format_duration(65)
        '0:01:05'
        
        >>> format_duration(65, show_hours=False)
        '01:05'
        
        >>> format_duration(3665)
        '1:01:05'
        
        >>> format_duration(90061)
        '25:01:01'
    """
    # Handle negative durations
    if seconds < 0:
        logger.warning(f"Negative duration: {seconds}")
        seconds = 0
    
    # Calculate hours, minutes, seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    # Format string
    if hours > 0 or show_hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_duration_verbose(seconds: int) -> str:
    """
    Format duration in seconds to verbose string.
    
    Examples: "5 seconds", "1 minute 30 seconds", "2 hours 15 minutes"
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        str: Verbose duration string
    
    Example:
        >>> format_duration_verbose(5)
        '5 seconds'
        
        >>> format_duration_verbose(90)
        '1 minute 30 seconds'
        
        >>> format_duration_verbose(3665)
        '1 hour 1 minute'
        
        >>> format_duration_verbose(7200)
        '2 hours'
    """
    if seconds < 0:
        seconds = 0
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    if secs > 0 or len(parts) == 0:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    
    # Join parts with proper grammar
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} {parts[1]}"
    else:
        # More than 2 parts: use commas
        return ", ".join(parts[:-1]) + f" and {parts[-1]}"


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to seconds.
    
    Supports formats:
    - "HH:MM:SS" (e.g., "1:30:45")
    - "MM:SS" (e.g., "5:30")
    - "SS" (e.g., "45")
    
    Args:
        duration_str: Duration string to parse
    
    Returns:
        int: Duration in seconds, 0 if parsing fails
    
    Example:
        >>> parse_duration("1:30:45")
        5445
        
        >>> parse_duration("5:30")
        330
        
        >>> parse_duration("45")
        45
    """
    try:
        parts = duration_str.strip().split(':')
        
        if len(parts) == 3:
            # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        
        elif len(parts) == 2:
            # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        
        elif len(parts) == 1:
            # SS
            return int(parts[0])
        
        else:
            logger.error(f"Invalid duration format: {duration_str}")
            return 0
    
    except ValueError as e:
        logger.error(f"Error parsing duration '{duration_str}': {e}")
        return 0


# ============================================================================
# TIME DIFFERENCE FUNCTIONS
# ============================================================================
def calculate_elapsed_time(start_time: datetime, end_time: Optional[datetime] = None) -> int:
    """
    Calculate elapsed time in seconds between two timestamps.
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp (default: current time)
    
    Returns:
        int: Elapsed seconds
    
    Example:
        >>> from datetime import datetime, timedelta
        >>> start = datetime.now() - timedelta(minutes=5)
        >>> elapsed = calculate_elapsed_time(start)
        >>> print(elapsed)
        300  # Approximately 5 minutes = 300 seconds
    """
    if end_time is None:
        end_time = datetime.now()
    
    delta = end_time - start_time
    return int(delta.total_seconds())


def time_ago(timestamp: datetime) -> str:
    """
    Get human-readable "time ago" string.
    
    Examples: "just now", "5 minutes ago", "2 hours ago", "3 days ago"
    
    Args:
        timestamp: Timestamp to compare to now
    
    Returns:
        str: Human-readable time ago string
    
    Example:
        >>> from datetime import datetime, timedelta
        >>> past = datetime.now() - timedelta(minutes=5)
        >>> print(time_ago(past))
        5 minutes ago
        
        >>> past = datetime.now() - timedelta(hours=2)
        >>> print(time_ago(past))
        2 hours ago
    """
    now = datetime.now()
    delta = now - timestamp
    
    seconds = int(delta.total_seconds())
    
    if seconds < 10:
        return "just now"
    elif seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = seconds // 604800
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = seconds // 2592000
        return f"{months} month{'s' if months != 1 else ''} ago"


# ============================================================================
# DATE RANGE FUNCTIONS
# ============================================================================
def get_date_range(days: int) -> Tuple[str, str]:
    """
    Get date range (start_date, end_date) for last N days.
    
    Args:
        days: Number of days to go back
    
    Returns:
        tuple: (start_date, end_date) as YYYY-MM-DD strings
    
    Example:
        >>> start, end = get_date_range(7)
        >>> # Returns dates for last 7 days
        >>> print(f"From {start} to {end}")
        From 2026-01-21 to 2026-01-28
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return (
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )


def is_same_day(dt1: datetime, dt2: datetime) -> bool:
    """
    Check if two datetimes are on the same day.
    
    Args:
        dt1: First datetime
        dt2: Second datetime
    
    Returns:
        bool: True if same day, False otherwise
    
    Example:
        >>> from datetime import datetime
        >>> dt1 = datetime(2026, 1, 28, 10, 0, 0)
        >>> dt2 = datetime(2026, 1, 28, 15, 0, 0)
        >>> is_same_day(dt1, dt2)
        True
    """
    return dt1.date() == dt2.date()


def is_today(dt: datetime) -> bool:
    """
    Check if datetime is today.
    
    Args:
        dt: Datetime to check
    
    Returns:
        bool: True if today, False otherwise
    
    Example:
        >>> from datetime import datetime
        >>> dt = datetime.now()
        >>> is_today(dt)
        True
    """
    return dt.date() == datetime.now().date()


def is_yesterday(dt: datetime) -> bool:
    """
    Check if datetime is yesterday.
    
    Args:
        dt: Datetime to check
    
    Returns:
        bool: True if yesterday, False otherwise
    
    Example:
        >>> from datetime import datetime, timedelta
        >>> dt = datetime.now() - timedelta(days=1)
        >>> is_yesterday(dt)
        True
    """
    yesterday = datetime.now().date() - timedelta(days=1)
    return dt.date() == yesterday


# ============================================================================
# RECORDING TIME FUNCTIONS
# ============================================================================
class RecordingTimer:
    """
    Timer class for tracking recording duration.
    
    Provides start/stop functionality and elapsed time calculation.
    Useful for displaying recording duration in real-time.
    
    Attributes:
        start_time (datetime): Recording start time
        end_time (datetime): Recording end time (None if still recording)
        is_recording (bool): Whether currently recording
    
    Example:
        >>> timer = RecordingTimer()
        >>> timer.start()
        >>> # ... recording happens ...
        >>> print(f"Duration: {timer.get_elapsed_formatted()}")
        Duration: 0:05:30
        >>> timer.stop()
        >>> print(f"Total: {timer.get_total_duration()} seconds")
        Total: 330
    """
    
    def __init__(self):
        """Initialize recording timer."""
        self.start_time = None
        self.end_time = None
        self.is_recording = False
    
    def start(self):
        """
        Start the timer.
        
        Example:
            >>> timer = RecordingTimer()
            >>> timer.start()
            >>> print(timer.is_recording)
            True
        """
        self.start_time = datetime.now()
        self.end_time = None
        self.is_recording = True
        logger.debug(f"Timer started at {self.start_time}")
    
    def stop(self):
        """
        Stop the timer.
        
        Example:
            >>> timer.start()
            >>> # ... some time passes ...
            >>> timer.stop()
            >>> print(timer.is_recording)
            False
        """
        if self.is_recording:
            self.end_time = datetime.now()
            self.is_recording = False
            logger.debug(f"Timer stopped at {self.end_time}")
        else:
            logger.warning("Timer.stop() called but timer not running")
    
    def reset(self):
        """
        Reset the timer.
        
        Example:
            >>> timer.reset()
            >>> print(timer.is_recording)
            False
        """
        self.start_time = None
        self.end_time = None
        self.is_recording = False
        logger.debug("Timer reset")
    
    def get_elapsed_seconds(self) -> int:
        """
        Get elapsed time in seconds.
        
        Returns:
            int: Elapsed seconds (0 if not started)
        
        Example:
            >>> timer.start()
            >>> time.sleep(5)
            >>> print(timer.get_elapsed_seconds())
            5
        """
        if self.start_time is None:
            return 0
        
        end = self.end_time if self.end_time else datetime.now()
        return calculate_elapsed_time(self.start_time, end)
    
    def get_elapsed_formatted(self, show_hours: bool = True) -> str:
        """
        Get elapsed time as formatted string.
        
        Args:
            show_hours: Always show hours even if 0
        
        Returns:
            str: Formatted duration (HH:MM:SS or MM:SS)
        
        Example:
            >>> timer.start()
            >>> time.sleep(65)
            >>> print(timer.get_elapsed_formatted())
            0:01:05
        """
        seconds = self.get_elapsed_seconds()
        return format_duration(seconds, show_hours)
    
    def get_total_duration(self) -> int:
        """
        Get total recording duration in seconds.
        
        Returns same as get_elapsed_seconds() for consistency.
        
        Returns:
            int: Total duration in seconds
        """
        return self.get_elapsed_seconds()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def sleep_until(target_time: datetime):
    """
    Sleep until a specific time.
    
    Args:
        target_time: Time to sleep until
    
    Example:
        >>> from datetime import datetime, timedelta
        >>> target = datetime.now() + timedelta(seconds=10)
        >>> sleep_until(target)
        >>> print("Woke up!")
    """
    now = datetime.now()
    
    if target_time <= now:
        logger.warning("Target time is in the past")
        return
    
    delta = (target_time - now).total_seconds()
    logger.debug(f"Sleeping for {delta} seconds")
    time.sleep(delta)


def get_year_month_day() -> Tuple[int, int, int]:
    """
    Get current year, month, day as tuple.
    
    Returns:
        tuple: (year, month, day)
    
    Example:
        >>> year, month, day = get_year_month_day()
        >>> print(f"{year}-{month:02d}-{day:02d}")
        2026-01-28
    """
    now = datetime.now()
    return (now.year, now.month, now.day)


# ============================================================================
# EXPORT
# ============================================================================
__all__ = [
    # Timestamp functions
    'get_timestamp',
    'get_date_string',
    'get_time_string',
    'parse_timestamp',
    
    # Duration functions
    'format_duration',
    'format_duration_verbose',
    'parse_duration',
    
    # Time difference
    'calculate_elapsed_time',
    'time_ago',
    
    # Date ranges
    'get_date_range',
    'is_same_day',
    'is_today',
    'is_yesterday',
    
    # Recording timer
    'RecordingTimer',
    
    # Utilities
    'sleep_until',
    'get_year_month_day',
]
