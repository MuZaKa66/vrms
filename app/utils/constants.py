"""
File: app/utils/constants.py

Module Description:
    Application-wide constants used throughout the codebase.
    
    Constants are grouped by category:
    - Status codes and states
    - Recording states
    - Error codes
    - UI constants
    - File type constants
    
    Using constants instead of magic strings/numbers provides:
    1. Single source of truth (change once, affect everywhere)
    2. Type safety and IDE autocomplete
    3. Self-documenting code
    4. Easy refactoring

Dependencies:
    - enum: For creating enumeration classes

Usage Example:
    >>> from app.utils.constants import RecordingState, ErrorCode
    >>> if recording_state == RecordingState.RECORDING:
    ...     print("Currently recording")

Author: OT Video Dev Team
Date: January 28, 2026
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
from enum import Enum, IntEnum, auto


# ============================================================================
# RECORDING STATES
# ============================================================================
class RecordingState(Enum):
    """
    Enumeration of possible recording states.
    
    States:
        IDLE: Not recording, ready to start
        STARTING: Recording initialization in progress
        RECORDING: Actively recording video
        PAUSED: Recording paused (feature for future)
        STOPPING: Stopping recording, finalizing file
        ERROR: Recording encountered an error
    
    Usage:
        >>> state = RecordingState.IDLE
        >>> if state == RecordingState.RECORDING:
        ...     print("Recording in progress")
    """
    IDLE = auto()
    CHECKING = auto()      # ADD THIS
    STARTING = auto()
    RECORDING = auto()
    PAUSED = auto()
    STOPPING = auto()
    SAVING = auto()        # ADD THIS
    ERROR = auto()


# ============================================================================
# APPLICATION STATES
# ============================================================================
class AppState(Enum):
    """
    Main application state machine states.
    
    States:
        INITIALIZING: App starting up, loading resources
        READY: App ready for user interaction
        BUSY: Performing background operation
        ERROR: App in error state
        SHUTTING_DOWN: App closing, cleanup in progress
    """
    INITIALIZING = auto()
    READY = auto()
    BUSY = auto()
    ERROR = auto()
    SHUTTING_DOWN = auto()


# ============================================================================
# ERROR CODES
# ============================================================================
class ErrorCode(IntEnum):
    """
    Standard error codes for consistent error handling.
    
    Using IntEnum allows comparing with integers and provides
    meaningful names for error conditions.
    
    Categories:
        0-99: Success and general errors
        100-199: Storage errors
        200-299: Video capture errors
        300-399: Audio/voice errors
        400-499: Database errors
        500-599: UI errors
    """
    # Success
    SUCCESS = 0
    
    # General errors (1-99)
    UNKNOWN_ERROR = 1
    INVALID_PARAMETER = 2
    OPERATION_CANCELLED = 3
    TIMEOUT = 4
    NOT_IMPLEMENTED = 5
    
    # Storage errors (100-199)
    STORAGE_NOT_MOUNTED = 100
    STORAGE_FULL = 101
    STORAGE_READ_ERROR = 102
    STORAGE_WRITE_ERROR = 103
    FILE_NOT_FOUND = 104
    FILE_EXISTS = 105
    PERMISSION_DENIED = 106
    
    # Video capture errors (200-299)
    VIDEO_DEVICE_NOT_FOUND = 200
    VIDEO_DEVICE_BUSY = 201
    VIDEO_CAPTURE_FAILED = 202
    VIDEO_ENCODING_FAILED = 203
    VIDEO_FORMAT_UNSUPPORTED = 204
    
    # Audio/voice errors (300-399)
    AUDIO_DEVICE_NOT_FOUND = 300
    AUDIO_DEVICE_BUSY = 301
    VOICE_MODEL_NOT_FOUND = 302
    VOICE_RECOGNITION_FAILED = 303
    
    # Database errors (400-499)
    DATABASE_NOT_FOUND = 400
    DATABASE_CONNECTION_FAILED = 401
    DATABASE_QUERY_FAILED = 402
    DATABASE_CONSTRAINT_VIOLATION = 403
    
    # UI errors (500-599)
    UI_INITIALIZATION_FAILED = 500
    UI_RESOURCE_NOT_FOUND = 501


# ============================================================================
# FILE TYPE CONSTANTS
# ============================================================================
# Video file extensions
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mkv', '.mov']

# Image file extensions
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

# Metadata file extensions
METADATA_EXTENSIONS = ['.json', '.xml', '.txt']


# ============================================================================
# UI CONSTANTS
# ============================================================================
# Screen names for navigation
class ScreenName:
    """Screen identifiers for navigation."""
    RECORDING = "recording"
    LIBRARY = "library"
    PLAYBACK = "playback"
    METADATA = "metadata"
    EXPORT = "export"
    SETTINGS = "settings"
    ABOUT = "about"


# Button sizes (pixels)
BUTTON_HEIGHT_SMALL = 40
BUTTON_HEIGHT_MEDIUM = 60
BUTTON_HEIGHT_LARGE = 80

# Icon sizes (pixels)
ICON_SIZE_SMALL = 24
ICON_SIZE_MEDIUM = 48
ICON_SIZE_LARGE = 96

# Spacing
SPACING_SMALL = 5
SPACING_MEDIUM = 10
SPACING_LARGE = 20

# Animation durations (milliseconds)
ANIMATION_DURATION_FAST = 150
ANIMATION_DURATION_MEDIUM = 300
ANIMATION_DURATION_SLOW = 500


# ============================================================================
# TIME CONSTANTS
# ============================================================================
# Duration constants in seconds
SECOND = 1
MINUTE = 60
HOUR = 3600
DAY = 86400

# Timeout constants
DEFAULT_TIMEOUT_SECONDS = 30
NETWORK_TIMEOUT_SECONDS = 10
DATABASE_TIMEOUT_SECONDS = 5


# ============================================================================
# STORAGE CONSTANTS
# ============================================================================
# Size constants in bytes
KB = 1024
MB = 1024 * KB
GB = 1024 * MB
TB = 1024 * GB

# Free space thresholds
MIN_FREE_SPACE_GB = 5
WARNING_FREE_SPACE_GB = 10
COMFORTABLE_FREE_SPACE_GB = 20


# ============================================================================
# VIDEO QUALITY PRESETS
# ============================================================================
class VideoQuality(Enum):
    """
    Video quality preset enumeration.
    
    Each preset defines bitrate settings for different quality levels.
    Higher bitrate = better quality but larger files.
    """
    LOW = "1M"      # 1 Mbps - smallest files
    MEDIUM = "2M"   # 2 Mbps - balanced
    HIGH = "3M"     # 3 Mbps - good quality (default)
    ULTRA = "5M"    # 5 Mbps - best quality, large files


# ============================================================================
# KEYBOARD SHORTCUTS (for development/debugging)
# ============================================================================
# Dictionary of keyboard shortcuts and their actions
KEYBOARD_SHORTCUTS = {
    'F1': 'help',
    'F5': 'refresh',
    'F11': 'toggle_fullscreen',
    'Ctrl+Q': 'quit',
    'Ctrl+S': 'save',
    'Space': 'toggle_recording',
    'Escape': 'cancel',
}


# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================
# Maximum lengths for text fields
MAX_PATIENT_NAME_LENGTH = 100
MAX_PROCEDURE_NAME_LENGTH = 200
MAX_SURGEON_NAME_LENGTH = 100
MAX_NOTES_LENGTH = 1000
MAX_TAG_LENGTH = 50
MAX_FILENAME_LENGTH = 255

# Regular expression patterns
PATIENT_NAME_PATTERN = r'^[A-Za-z0-9\s\-\.]+$'
FILENAME_SAFE_PATTERN = r'^[A-Za-z0-9_\-\.]+$'


# ============================================================================
# DEFAULT VALUES
# ============================================================================
# Default values for various settings
DEFAULT_VOLUME = 0.8
DEFAULT_BRIGHTNESS = 100
DEFAULT_TIMEOUT_MINUTES = 5

# Placeholder text
PLACEHOLDER_PATIENT_NAME = "Enter patient name"
PLACEHOLDER_PROCEDURE = "Enter procedure name"
PLACEHOLDER_NOTES = "Add notes here..."


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def get_error_message(error_code):
    """
    Get human-readable error message for error code.
    
    Args:
        error_code (ErrorCode): Error code enum value
    
    Returns:
        str: User-friendly error message
    
    Example:
        >>> msg = get_error_message(ErrorCode.STORAGE_FULL)
        >>> print(msg)
        Storage is full. Please free up space or export videos.
    """
    messages = {
        ErrorCode.SUCCESS: "Operation completed successfully",
        ErrorCode.UNKNOWN_ERROR: "An unknown error occurred",
        ErrorCode.STORAGE_FULL: "Storage is full. Please free up space or export videos.",
        ErrorCode.VIDEO_DEVICE_NOT_FOUND: "Video capture device not found. Check USB connection.",
        ErrorCode.AUDIO_DEVICE_NOT_FOUND: "Microphone not found. Check USB connection.",
        ErrorCode.DATABASE_NOT_FOUND: "Database not found. Please run database initialization.",
        # Add more as needed
    }
    
    return messages.get(error_code, f"Error code: {error_code}")


# ============================================================================
# EXPORT
# ============================================================================
# Export all constants for easy import
__all__ = [
    # Enums
    'RecordingState',
    'AppState',
    'ErrorCode',
    'VideoQuality',
    'ScreenName',
    
    # File extensions
    'VIDEO_EXTENSIONS',
    'IMAGE_EXTENSIONS',
    
    'METADATA_EXTENSIONS',
    
    # Sizes
    'KB', 'MB', 'GB', 'TB',
    
    # Time
    'SECOND', 'MINUTE', 'HOUR', 'DAY',
    
    # UI
    'BUTTON_HEIGHT_SMALL', 'BUTTON_HEIGHT_MEDIUM', 'BUTTON_HEIGHT_LARGE',
    'ICON_SIZE_SMALL', 'ICON_SIZE_MEDIUM', 'ICON_SIZE_LARGE',
    
    # Functions
    'get_error_message',
]
