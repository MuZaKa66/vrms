#python
"""
File: app/utils/logger.py

Module Description:
    Comprehensive logging system for the OT Video Management System.
    
    Features:
    - Dual logging: console (for development) and file (for production)
    - Automatic log rotation (by size and date)
    - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Colored console output (optional)
    - Module-specific loggers with inherited configuration
    
    Log files are stored in logs/ directory with daily rotation.
    Each module can create its own logger with consistent formatting.

Dependencies:
    - logging: Python standard library
    - datetime: For timestamping
    - pathlib: For path handling

Usage Example:
    >>> from app.utils.logger import AppLogger
    >>> logger = AppLogger("MyModule")
    >>> logger.info("Application started")
    >>> logger.error("Something went wrong", exc_info=True)

Author: OT Video Dev Team
Date: January 28, 2026
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Import configuration
from config.app_config import (
    LOGS_DIR,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    LOG_MAX_FILE_SIZE_MB,
    LOG_BACKUP_COUNT,
    APP_NAME
)


# ============================================================================
# CONSTANTS
# ============================================================================
# ANSI color codes for console output (optional, for development)
COLOR_RESET = '\033[0m'
COLOR_DEBUG = '\033[36m'    # Cyan
COLOR_INFO = '\033[32m'     # Green
COLOR_WARNING = '\033[33m'  # Yellow
COLOR_ERROR = '\033[31m'    # Red
COLOR_CRITICAL = '\033[35m' # Magenta


# ============================================================================
# COLORED FORMATTER (for console output)
# ============================================================================
class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console log messages.
    
    Different log levels are displayed in different colors for easy
    visual identification during development.
    
    Only used for console output, not for file logging.
    """
    
    # Map log levels to colors
    COLORS = {
        'DEBUG': COLOR_DEBUG,
        'INFO': COLOR_INFO,
        'WARNING': COLOR_WARNING,
        'ERROR': COLOR_ERROR,
        'CRITICAL': COLOR_CRITICAL,
    }
    
    def format(self, record):
        """
        Format log record with color codes.
        
        Args:
            record: LogRecord to format
        
        Returns:
            str: Formatted log message with color codes
        """
        # Get color for this log level
        color = self.COLORS.get(record.levelname, COLOR_RESET)
        
        # Add color to level name
        original_levelname = record.levelname
        record.levelname = f"{color}{record.levelname}{COLOR_RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Restore original level name
        record.levelname = original_levelname
        
        return formatted


# ============================================================================
# LOGGER CLASS
# ============================================================================
class AppLogger:
    """
    Application logger class providing consistent logging across modules.
    
    Each module can create its own logger instance with a unique name.
    All loggers share the same configuration (format, handlers, level).
    
    Features:
    - Dual output: console and file
    - Automatic file rotation
    - Module-specific names
    - Consistent formatting
    - Easy to use interface
    
    Attributes:
        logger (logging.Logger): Underlying Python logger instance
        name (str): Logger name (usually module name)
    
    Example:
        >>> logger = AppLogger("RecordingController")
        >>> logger.info("Recording started")
        2026-01-28 14:30:22 - RecordingController - INFO - Recording started
    """
    
    # Class variable to track if handlers have been configured
    # This ensures handlers are only added once, even if multiple
    # AppLogger instances are created
    _handlers_configured = False
    
    def __init__(self, name="OTVideo"):
        """
        Initialize logger instance.
        
        Args:
            name (str): Logger name (typically module name)
                       Used to identify which part of code generated log
        
        Example:
            >>> logger = AppLogger("VideoCapture")
            >>> logger.info("Initializing video capture")
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Set log level from configuration
        log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Configure handlers if not already done
        # This prevents duplicate handlers when creating multiple loggers
        if not AppLogger._handlers_configured:
            self._setup_handlers()
            AppLogger._handlers_configured = True
    
    def _setup_handlers(self):
        """
        Set up file and console handlers for logging.
        
        This method:
        1. Creates logs directory if it doesn't exist
        2. Sets up rotating file handler (rotates by size)
        3. Sets up console handler for development
        4. Applies formatting to both handlers
        
        Called automatically during initialization.
        """
        # ====================================================================
        # STEP 1: Ensure logs directory exists
        # ====================================================================
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # If we can't create log directory, print to stderr
            # but don't crash the application
            print(f"Warning: Could not create logs directory: {e}", file=sys.stderr)
        
        # ====================================================================
        # STEP 2: Set up file handler with rotation
        # ====================================================================
        # Create log filename with today's date
        # Format: otvideo_20260128.log
        log_filename = LOGS_DIR / f"otvideo_{datetime.now().strftime('%Y%m%d')}.log"
        
        try:
            # Rotating file handler: rotates when file size exceeds limit
            # Keeps specified number of backup files
            file_handler = RotatingFileHandler(
                filename=log_filename,
                maxBytes=LOG_MAX_FILE_SIZE_MB * 1024 * 1024,  # Convert MB to bytes
                backupCount=LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            
            # Set log level for file (usually same as logger level)
            file_handler.setLevel(logging.DEBUG)
            
            # Create formatter for file output
            file_formatter = logging.Formatter(
                fmt=LOG_FORMAT,
                datefmt=LOG_DATE_FORMAT
            )
            file_handler.setFormatter(file_formatter)
            
            # Add file handler to root logger
            # Using root logger ensures all loggers write to same file
            logging.getLogger().addHandler(file_handler)
            
        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)
        
        # ====================================================================
        # STEP 3: Set up console handler
        # ====================================================================
        # Console output is helpful during development
        # In production, you might want to disable this or increase level to WARNING
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Only INFO and above to console
        
        # Use colored formatter for console (easier to read)
        console_formatter = ColoredFormatter(
            fmt=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )
        console_handler.setFormatter(console_formatter)
        
        # Add console handler to root logger
        logging.getLogger().addHandler(console_handler)
    
    # ========================================================================
    # LOGGING METHODS
    # ========================================================================
    # These methods wrap the standard logging methods with a cleaner interface
    
    def debug(self, message, *args, **kwargs):
        """
        Log debug message.
        
        Debug level: Detailed information for diagnosing problems.
        Use for: Internal state, variable values, flow control.
        
        Args:
            message (str): Log message
            *args: Variable arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Example:
            >>> logger.debug("Processing frame %d", frame_number)
            >>> logger.debug("State changed", extra={'state': new_state})
        """
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """
        Log info message.
        
        Info level: Confirmation that things are working as expected.
        Use for: Major events, state changes, successful operations.
        
        Args:
            message (str): Log message
            *args: Variable arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Example:
            >>> logger.info("Recording started successfully")
            >>> logger.info("Video saved: %s", filename)
        """
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """
        Log warning message.
        
        Warning level: Something unexpected but not critical.
        Use for: Degraded performance, approaching limits, workarounds.
        
        Args:
            message (str): Log message
            *args: Variable arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Example:
            >>> logger.warning("Storage space low: %d GB free", free_space_gb)
            >>> logger.warning("Frame dropped during encoding")
        """
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """
        Log error message.
        
        Error level: Error occurred but application can continue.
        Use for: Failed operations, caught exceptions, recoverable errors.
        
        Args:
            message (str): Log message
            *args: Variable arguments for message formatting
            **kwargs: Keyword arguments passed to logger
                     Use exc_info=True to include exception traceback
        
        Example:
            >>> logger.error("Failed to save video", exc_info=True)
            >>> logger.error("Database query failed: %s", error_msg)
        """
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """
        Log critical message.
        
        Critical level: Severe error, application may not continue.
        Use for: Fatal errors, unrecoverable states, data corruption.
        
        Args:
            message (str): Log message
            *args: Variable arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Example:
            >>> logger.critical("Database corrupted, cannot continue")
            >>> logger.critical("Out of memory", exc_info=True)
        """
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message, *args, **kwargs):
        """
        Log exception message with traceback.
        
        Convenience method that automatically includes exception information.
        Should be called from exception handler.
        
        Args:
            message (str): Log message
            *args: Variable arguments for message formatting
            **kwargs: Keyword arguments passed to logger
        
        Example:
            >>> try:
            ...     risky_operation()
            ... except Exception as e:
            ...     logger.exception("Operation failed")
        """
        # exception() is same as error() with exc_info=True
        self.logger.exception(message, *args, **kwargs)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def log_system_info(self):
        """
        Log system information for debugging.
        
        Logs useful system information like:
        - Python version
        - Operating system
        - Application version
        - Current time
        
        Useful to call at application startup.
        
        Example:
            >>> logger = AppLogger("Main")
            >>> logger.log_system_info()
        """
        import platform
        from config.app_config import APP_NAME, APP_VERSION
        
        self.info("=" * 60)
        self.info(f"{APP_NAME} v{APP_VERSION}")
        self.info(f"Python {platform.python_version()}")
        self.info(f"Platform: {platform.platform()}")
        self.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("=" * 60)
    
    def log_separator(self, char='-', length=60):
        """
        Log a separator line for visual organization.
        
        Args:
            char (str): Character to use for separator
            length (int): Length of separator line
        
        Example:
            >>> logger.log_separator()
            >>> logger.info("New section")
            >>> logger.log_separator('=')
        """
        self.info(char * length)


# ============================================================================
# MODULE-LEVEL FUNCTIONS
# ============================================================================
def get_logger(name):
    """
    Get a logger instance for a module.
    
    Convenience function for creating loggers.
    Equivalent to AppLogger(name) but more concise.
    
    Args:
        name (str): Logger name (typically __name__ of module)
    
    Returns:
        AppLogger: Logger instance
    
    Example:
        >>> from app.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return AppLogger(name)


def disable_console_logging():
    """
    Disable console logging output.
    
    Useful in production to reduce console output.
    File logging continues normally.
    
    Example:
        >>> from app.utils.logger import disable_console_logging
        >>> disable_console_logging()
    """
    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.CRITICAL + 1)  # Effectively disable


def enable_debug_logging():
    """
    Enable debug level logging for all loggers.
    
    Useful for troubleshooting.
    
    Example:
        >>> from app.utils.logger import enable_debug_logging
        >>> enable_debug_logging()
    """
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)


# ============================================================================
# MAIN EXECUTION (for testing logger)
# ============================================================================
if __name__ == "__main__":
    """
    Test logging functionality.
    
    Run this file directly to test the logging system:
        python3 app/utils/logger.py
    """
    # Create test logger
    logger = AppLogger("LoggerTest")
    
    # Test all log levels
    logger.log_system_info()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("Caught an exception")
    
    logger.log_separator()
    logger.info("Logger test complete")