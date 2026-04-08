"""
File: config/app_config.py

Module Description:
    Central configuration file for the VRMS (Video Recording Management System).
    Contains all application settings, paths, and constants.
    
    This file should be the single source of truth for all configuration.
    Any module that needs configuration values should import from here.
    
    Configuration is organized into sections:
    1. FORCE_MANUAL_CONFIG Flag - Enable/disable auto-detection
    2. PLATFORM AUTO-DETECTION - Automatic platform detection logic
    3. MANUAL OVERRIDE SECTION - User-editable values (when auto-detection disabled)
    4. APPLICATION METADATA - Name, version, author
    5. DIRECTORY PATHS - Application directory structure
    6. STORAGE PATHS - Video storage locations
    7. VIDEO CAPTURE SETTINGS - Camera and encoding
    8. AUDIO SETTINGS - Microphone configuration
    9. VOICE RECOGNITION SETTINGS - Vosk model and commands
    10. STORAGE SETTINGS - Space management and backups
    11. SYSTEM SETTINGS - Monitoring thresholds
    12. GUI SETTINGS - Window and theme
    13. DEBUG AND LOGGING SETTINGS - Log levels and rotation
    14. FEATURE FLAGS - Feature toggles
    15. VALIDATION AND UTILITIES - Path validation functions
    15.5: STORAGE DEVICE DETECTION (Boot Resilience)
    16. CONFIGURATION NOTES - Platform switching guide
    17. MODULE INITIALIZATION - Auto-validation on import
    18. MAIN EXECUTION - Self-test when run directly

Dependencies:
    - os: For path manipulation
    - pathlib: For modern path handling
    - No external dependencies (this is imported by everything else)

Usage Example:
    >>> from config.app_config import VIDEO_WIDTH, VIDEO_HEIGHT
    >>> print(f"Video resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT}")
    Video resolution: 720x480

Author: OT Video Dev Team
Date: March 24, 2026
Version: 1.1.0
Last Updated: April 8, 2026
Changelog:
    - v1.1.0: Added platform auto-detection, FORCE_MANUAL_CONFIG flag, manual override section
    - v1.0.2: Added LOG_DATE_FORMAT and compatibility aliases for logger.py
    - v1.0.1: Added RECORDINGS_DIR constant for compatibility with updated playback_screen.py
"""

# ============================================================================
# IMPORTS
# ============================================================================
import os
from pathlib import Path


# ============================================================================
# SECTION 1: FORCE MANUAL CONFIGURATION FLAG
# ============================================================================
# Set to True to ignore auto-detection and use manually defined values in SECTION 3
# Set to False (default) to auto-select optimal settings based on platform
#
# WHEN TO USE:
#   - False: Normal operation - auto-detects Windows vs Raspberry Pi
#   - True:  Testing or special hardware - force specific values
#
FORCE_MANUAL_CONFIG = False


# ============================================================================
# SECTION 2: PLATFORM AUTO-DETECTION FUNCTION
# ============================================================================

def get_platform_config():
    """
    Auto-detect platform and return optimal configuration values.
    
    This function automatically selects the best settings for the current platform:
    - Windows/Laptop development: OpenCV encoder, local storage, camera index
    - Raspberry Pi production: Hardware encoder, SSD storage path, device file
    
    The auto-detection can be disabled by setting FORCE_MANUAL_CONFIG = True,
    which forces the use of manually defined values in SECTION 3.
    
    Returns:
        dict: Platform-specific configuration dictionary with the following keys:
            - video_storage_path (Path): Path to video storage directory
            - video_device (str/int): Video device (string path for Linux, int index for Windows)
            - use_opencv_encoder (bool): True for OpenCV, False for FFmpeg hardware encoding
            - video_encoder (str): Encoder name for FFmpeg (e.g., 'h264_v4l2m2m' or 'libx264')
            - video_width (int): Optimal width for platform
            - video_height (int): Optimal height for platform
            - video_fps (int): Optimal frame rate for platform
            - platform_name (str): Human-readable platform name
            - is_raspberry_pi (bool): True if running on Raspberry Pi
            - is_windows (bool): True if running on Windows
            - is_linux (bool): True if running on Linux
    
    Example:
        >>> config = get_platform_config()
        >>> if config['is_raspberry_pi']:
        ...     print(f"Pi detected - using hardware encoder: {config['video_encoder']}")
        >>> print(f"Storage path: {config['video_storage_path']}")
        Storage path: /mnt/videostore
    """
    import platform
    from pathlib import Path
    
    # Initialize with default values (safe fallback)
    result = {
        'video_storage_path': Path("./videostore"),
        'video_device': 0,
        'use_opencv_encoder': True,
        'video_encoder': 'libx264',
        'video_width': 1024,
        'video_height': 600,
        'video_fps': 30,
        'platform_name': 'Unknown',
        'is_raspberry_pi': False,
        'is_windows': False,
        'is_linux': False,
    }
    
    # Detect operating system
    system = platform.system()
    result['is_windows'] = (system == 'Windows')
    result['is_linux'] = (system == 'Linux')
    
    # Detect Raspberry Pi (Linux with specific hardware)
    is_pi = False
    pi_model = ""
    
    if system == 'Linux':
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                is_pi = 'Raspberry Pi' in model
                pi_model = model.strip()
        except (FileNotFoundError, PermissionError, IOError):
            pass
        
        if not is_pi:
            try:
                with open('/sys/firmware/devicetree/base/model', 'r') as f:
                    model = f.read()
                    is_pi = 'Raspberry Pi' in model
                    pi_model = model.strip()
            except (FileNotFoundError, PermissionError, IOError):
                pass
    
    result['is_raspberry_pi'] = is_pi
    
    # Set platform name for logging
    if is_pi:
        result['platform_name'] = f"Raspberry Pi ({pi_model})"
    elif system == 'Windows':
        result['platform_name'] = f"Windows {platform.release()}"
    elif system == 'Linux':
        result['platform_name'] = f"Linux {platform.release()}"
    else:
        result['platform_name'] = f"{system} {platform.release()}"
    
    # ========================================================================
    # AUTO-CONFIGURE PLATFORM-SPECIFIC SETTINGS
    # ========================================================================
    
    if is_pi:
        # ====================================================================
        # RASPBERRY PI PRODUCTION CONFIGURATION
        # ====================================================================
        # These settings are optimized for Pi 4 with CVBS input and SSD storage
        # ====================================================================
        
        # Storage: External SSD mounted at /mnt/videostore (production)
        result['video_storage_path'] = Path("/mnt/videostore")
        
        # Video device: CVBS capture device (USB video grabber)
        result['video_device'] = "/dev/video0"
        
        # Encoder: Use FFmpeg with hardware encoder for optimal performance
        result['use_opencv_encoder'] = False
        result['video_encoder'] = "h264_v4l2m2m"  # Pi hardware encoder
        
        # Video resolution: NTSC standard 720x480
        result['video_width'] = 720
        result['video_height'] = 480
        
        # Frame rate: NTSC standard 30 fps
        result['video_fps'] = 30
        
        # Validate Pi storage mount point (warning only)
        if not result['video_storage_path'].exists():
            import warnings
            warnings.warn(
                f"Pi storage path not found: {result['video_storage_path']}. "
                f"Falling back to local storage.",
                RuntimeWarning
            )
            result['video_storage_path'] = Path("./videostore")
        
        # Check if hardware encoder is available (optional validation)
        try:
            import subprocess
            result_ffmpeg = subprocess.run(
                ['ffmpeg', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'h264_v4l2m2m' not in result_ffmpeg.stdout:
                import warnings
                warnings.warn(
                    "Pi hardware encoder (h264_v4l2m2m) not found. "
                    "Falling back to libx264 software encoder.",
                    RuntimeWarning
                )
                result['video_encoder'] = 'libx264'
        except (subprocess.SubprocessError, FileNotFoundError):
            # ffmpeg not found - use default
            pass
    
    else:
        # ====================================================================
        # WINDOWS / DEVELOPMENT CONFIGURATION
        # ====================================================================
        # These settings are optimized for laptop development and testing
        # ====================================================================
        
        # Storage: Local folder for development
        result['video_storage_path'] = Path("./videostore")
        
        # Video device: Camera index (0 = built-in webcam)
        result['video_device'] = 0
        
        # Encoder: OpenCV is reliable and cross-platform
        result['use_opencv_encoder'] = True
        result['video_encoder'] = "libx264"
        
        # Video resolution: Lower for development CPU load
        result['video_width'] = 640
        result['video_height'] = 480
        
        # Frame rate: Standard 30 fps
        result['video_fps'] = 30
    
    # Ensure storage path is absolute if relative
    if not result['video_storage_path'].is_absolute():
        result['video_storage_path'] = Path.cwd() / result['video_storage_path']
    
    # Validate video device exists (warning only for string paths)
    if isinstance(result['video_device'], str) and result['video_device']:
        if not Path(result['video_device']).exists():
            import warnings
            warnings.warn(
                f"Video device not found: {result['video_device']}. "
                f"Camera may not be connected.",
                RuntimeWarning
            )
    
    return result


# ============================================================================
# SECTION 3: MANUAL OVERRIDE SECTION
# ============================================================================
# IMPORTANT: These values are ONLY used when FORCE_MANUAL_CONFIG = True
#            When FORCE_MANUAL_CONFIG = False, values are auto-detected above
#
# To manually configure:
#   1. Set FORCE_MANUAL_CONFIG = True (at top of this file)
#   2. Uncomment and modify the desired values below
#   3. Save and run the application
#
# ============================================================================

# ----------------------------------------------------------------------------
# STORAGE PATHS - Manual Override (uncomment to use)
# ----------------------------------------------------------------------------
# VIDEO_STORAGE_PATH = Path("/mnt/videostore")  # Pi: external SSD
# VIDEO_STORAGE_PATH = Path("./videostore")     # Windows: local folder

# ----------------------------------------------------------------------------
# VIDEO CAPTURE SETTINGS - Manual Override (uncomment to use)
# ----------------------------------------------------------------------------
# VIDEO_DEVICE = "/dev/video0"  # Pi: CVBS capture device
VIDEO_DEVICE = 0              # Windows: camera index
# VIDEO_WIDTH = 640             # NTSC standard
VIDEO_HEIGHT = 480            # NTSC standard
VIDEO_FPS = 30                # Frames per second

# ----------------------------------------------------------------------------
# ENCODER SETTINGS - Manual Override (uncomment to use)
# ----------------------------------------------------------------------------
USE_OPENCV_ENCODER = True    # False = FFmpeg, True = OpenCV
# VIDEO_ENCODER = "h264_v4l2m2m"  # Pi hardware encoder
VIDEO_ENCODER = "libx264"        # Software encoder

# ============================================================================
# SECTION 4: APPLY CONFIGURATION (Auto-detection or Manual Override)
# ============================================================================

# Get platform-optimized configuration
_platform_config = get_platform_config()

# Apply configuration based on FORCE_MANUAL_CONFIG flag
if not FORCE_MANUAL_CONFIG:
    # Auto-detection mode: Use platform-optimized values
    VIDEO_STORAGE_PATH = _platform_config['video_storage_path']
    VIDEO_DEVICE = _platform_config['video_device']
    USE_OPENCV_ENCODER = _platform_config['use_opencv_encoder']
    VIDEO_ENCODER = _platform_config['video_encoder']
    VIDEO_WIDTH = _platform_config['video_width']
    VIDEO_HEIGHT = _platform_config['video_height']
    VIDEO_FPS = _platform_config['video_fps']
else:
    # Manual override mode: Use values from SECTION 3 if defined
    # Check each manual value using globals() to avoid NameError
    manual_values_defined = False
    
    # VIDEO_STORAGE_PATH
    if 'VIDEO_STORAGE_PATH' in globals():
        VIDEO_STORAGE_PATH = globals()['VIDEO_STORAGE_PATH']
        manual_values_defined = True
    else:
        VIDEO_STORAGE_PATH = _platform_config['video_storage_path']
    
    # VIDEO_DEVICE
    if 'VIDEO_DEVICE' in globals():
        VIDEO_DEVICE = globals()['VIDEO_DEVICE']
        manual_values_defined = True
    else:
        VIDEO_DEVICE = _platform_config['video_device']
    
    # USE_OPENCV_ENCODER
    if 'USE_OPENCV_ENCODER' in globals():
        USE_OPENCV_ENCODER = globals()['USE_OPENCV_ENCODER']
        manual_values_defined = True
    else:
        USE_OPENCV_ENCODER = _platform_config['use_opencv_encoder']
    
    # VIDEO_ENCODER
    if 'VIDEO_ENCODER' in globals():
        VIDEO_ENCODER = globals()['VIDEO_ENCODER']
        manual_values_defined = True
    else:
        VIDEO_ENCODER = _platform_config['video_encoder']
    
    # VIDEO_WIDTH
    if 'VIDEO_WIDTH' in globals():
        VIDEO_WIDTH = globals()['VIDEO_WIDTH']
        manual_values_defined = True
    else:
        VIDEO_WIDTH = _platform_config['video_width']
    
    # VIDEO_HEIGHT
    if 'VIDEO_HEIGHT' in globals():
        VIDEO_HEIGHT = globals()['VIDEO_HEIGHT']
        manual_values_defined = True
    else:
        VIDEO_HEIGHT = _platform_config['video_height']
    
    # VIDEO_FPS
    if 'VIDEO_FPS' in globals():
        VIDEO_FPS = globals()['VIDEO_FPS']
        manual_values_defined = True
    else:
        VIDEO_FPS = _platform_config['video_fps']
    
    # Show warning if no manual values were defined
    if not manual_values_defined:
        import warnings
        warnings.warn(
            "FORCE_MANUAL_CONFIG = True but no manual values set in SECTION 3. "
            "Using auto-detected values. To use manual values, uncomment them in SECTION 3.",
            RuntimeWarning
        )


# ============================================================================
# SECTION 5: APPLICATION METADATA
# ============================================================================
APP_NAME = "Video Recording Management System (VRMS)"
APP_VERSION = "1.1.0"
APP_AUTHOR = "OT Video Dev Team"
APP_DESCRIPTION = "Video recording and management for operating theatre microscopes"


# ============================================================================
# SECTION 6: DIRECTORY PATHS
# ============================================================================
# Application directory structure
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"
TESTS_DIR = BASE_DIR / "tests"
DOCS_DIR = BASE_DIR / "docs"

# Asset subdirectories
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"


# ============================================================================
# SECTION 7: STORAGE PATHS
# ============================================================================
# Storage subdirectories for video files
VIDEO_DIR = VIDEO_STORAGE_PATH / "videos"  # Legacy location (backwards compatibility)
RECORDINGS_DIR = VIDEO_STORAGE_PATH / "recordings"  # Primary recordings directory
THUMBNAIL_DIR = VIDEO_STORAGE_PATH / "thumbnails"  # Video thumbnail images
TEMP_DIR = str(Path(VIDEO_STORAGE_PATH) / "temp")  # Temporary files during recording
DATABASE_DIR = VIDEO_STORAGE_PATH / "database"  # SQLite database storage
BACKUP_DIR = VIDEO_STORAGE_PATH / "metadata_backup"  # Database backups

# Database file path
DATABASE_NAME = "otvideo.db"
DATABASE_PATH = DATABASE_DIR / DATABASE_NAME


# ============================================================================
# SECTION 8: VIDEO CAPTURE SETTINGS
# ============================================================================
# Video codec and encoding settings
VIDEO_CODEC = "h264"  # H.264/AVC compression standard

# Video encoding quality
VIDEO_BITRATE = "3M"  # 3 Mbps - good quality for standard definition

# Video file format
VIDEO_FILE_EXTENSION = ".mp4"  # MPEG-4 container
VIDEO_PIXEL_FORMAT = "yuv420p"  # Standard YUV color space for H.264

# Recording constraints (safety limits)
MIN_RECORDING_DURATION_SECONDS = 5  # Minimum 5 seconds
MAX_RECORDING_DURATION_MINUTES = 120  # Maximum 2 hours per recording
MAX_RECORDING_DURATION_SECONDS = MAX_RECORDING_DURATION_MINUTES * 60


# ============================================================================
# SECTION 9: AUDIO SETTINGS
# ============================================================================
AUDIO_DEVICE = "default"  # System default audio input
AUDIO_CHANNELS = 1  # Mono (sufficient for voice recognition)
AUDIO_RATE = 44100  # 44.1 kHz sample rate
AUDIO_CHUNK_SIZE = 1024  # Buffer size for audio processing

# Audio feedback settings
AUDIO_FEEDBACK_ENABLED = True  # Play sound effects
AUDIO_FEEDBACK_VOLUME = 0.8  # Volume level (0.0 to 1.0)


# ============================================================================
# SECTION 10: VOICE RECOGNITION SETTINGS
# ============================================================================
# Vosk offline speech recognition model
VOSK_MODEL_PATH = Path.home() / "vosk-models" / "vosk-model-small-en-us-0.15"

# Voice recognition parameters
#VOICE_RECOGNITION_ENABLED = True  # commented to avoid duplication wrt flag settings (sec 15)
VOICE_CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence score (0.0 to 1.0)
VOICE_COMMAND_TIMEOUT_SECONDS = 5  # Max time to wait for command completion

# Supported voice commands
VOICE_COMMANDS = {
    "start_recording": ["start recording", "begin recording", "record"],
    "stop_recording": ["stop recording", "end recording", "stop"],
    "patient_name": ["patient name", "patient"],
    "procedure": ["procedure", "operation"],
    "operating_theatre": ["operating theatre", "o t", "theater"],
    "surgeon": ["surgeon", "doctor"],
    "cancel": ["cancel", "nevermind", "never mind"],
}


# ============================================================================
# SECTION 11: STORAGE SETTINGS
# ============================================================================
# Storage space management
STORAGE_WARNING_THRESHOLD_GB = 10  # Warn when less than 10 GB free
STORAGE_CRITICAL_THRESHOLD_GB = 5  # Block new recordings when less than 5 GB free

# Thumbnail settings
THUMBNAIL_WIDTH = 320
THUMBNAIL_HEIGHT = 240
THUMBNAIL_QUALITY = 85  # JPEG quality (0-100)

# Video file naming convention
VIDEO_FILENAME_DATE_FORMAT = "%Y%m%d_%H%M%S"

# Backup settings
AUTO_BACKUP_ENABLED = True
AUTO_BACKUP_INTERVAL_HOURS = 24
MAX_BACKUP_FILES = 7


# ============================================================================
# SECTION 12: SYSTEM SETTINGS
# ============================================================================
# System monitoring thresholds
CPU_TEMP_WARNING_CELSIUS = 70
CPU_TEMP_CRITICAL_CELSIUS = 80
MEMORY_WARNING_THRESHOLD_PERCENT = 80

# System monitor update interval
SYSTEM_MONITOR_INTERVAL_SECONDS = 5

# Watchdog settings (Raspberry Pi only)
WATCHDOG_ENABLED = False
WATCHDOG_TIMEOUT_SECONDS = 30


# ============================================================================
# SECTION 13: GUI SETTINGS
# ============================================================================
# Window configuration
WINDOW_TITLE = APP_NAME
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 600
WINDOW_FULLSCREEN = False  # Set True for production kiosk mode

# Theme and styling
THEME_COLOR_PRIMARY = "#2196F3"  # Blue
THEME_COLOR_SECONDARY = "#FFC107"  # Amber
THEME_COLOR_SUCCESS = "#4CAF50"  # Green
THEME_COLOR_WARNING = "#FF9800"  # Orange
THEME_COLOR_DANGER = "#F44336"  # Red
THEME_COLOR_BACKGROUND = "#FFFFFF"  # White
THEME_COLOR_TEXT = "#212121"  # Dark grey

# Button sizes (optimized for touchscreen)
BUTTON_HEIGHT = 60
BUTTON_FONT_SIZE = 14

# Preview settings
PREVIEW_UPDATE_INTERVAL_MS = 100  # 10 fps
PREVIEW_SCALE_FACTOR = 0.5

# Timeline settings
TIMELINE_HEIGHT = 40


# ============================================================================
# SECTION 14: DEBUG AND LOGGING SETTINGS
# ============================================================================
# Debug mode
DEBUG_MODE = True  # Set False for production

# Logging configuration
LOG_LEVEL_CONSOLE = "INFO"
LOG_LEVEL_FILE = "DEBUG"
LOG_FILE_MAX_SIZE_MB = 10
LOG_FILE_BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Compatibility aliases for logger.py (DO NOT REMOVE)
LOG_LEVEL = LOG_LEVEL_FILE
LOG_MAX_FILE_SIZE_MB = LOG_FILE_MAX_SIZE_MB
LOG_BACKUP_COUNT = LOG_FILE_BACKUP_COUNT

# Performance monitoring
ENABLE_PERFORMANCE_MONITORING = True
PERFORMANCE_LOG_INTERVAL_SECONDS = 10


# ============================================================================
# SECTION 15: FEATURE FLAGS
# ============================================================================
ENABLE_VOICE_COMMANDS = True
ENABLE_METADATA_ENTRY = True
ENABLE_USB_EXPORT = True
ENABLE_SYSTEM_MONITORING = True
ENABLE_AUTO_BACKUP = True

# ============================================================================
# SECTION 15.5: STORAGE DEVICE DETECTION (Boot Resilience)
# ============================================================================

def detect_boot_device():
    """
    Detect current boot device (SSD primary, SD card fallback).
    
    On Raspberry Pi:
        - Checks /boot/cmdline.txt for root device
        - Detects if booting from SSD (USB) or SD card
    On Windows:
        - Returns simulated value for development
    
    Returns:
        dict: {
            'boot_device': str,  # 'ssd', 'sdcard', or 'unknown'
            'boot_path': str,    # device path or mount point
            'is_fallback': bool, # True if running from fallback device
            'error': str or None
        }
    """
    import platform
    import os
    
    result = {
        'boot_device': 'unknown',
        'boot_path': 'unknown',
        'is_fallback': False,
        'error': None
    }
    
    system = platform.system()
    
    if system == 'Windows':
        # Windows development - simulate SSD as primary
        result['boot_device'] = 'ssd'
        result['boot_path'] = 'C:\\'
        result['is_fallback'] = False
        result['error'] = None
        
    elif system == 'Linux':
        # Raspberry Pi detection
        try:
            # Read kernel command line to find root device
            with open('/proc/cmdline', 'r') as f:
                cmdline = f.read()
            
            # Look for root= parameter
            import re
            root_match = re.search(r'root=([^\s]+)', cmdline)
            
            if root_match:
                root_device = root_match.group(1)
                result['boot_path'] = root_device
                
                # SSD detection: USB devices typically /dev/sda or /dev/sdb
                # SD card detection: /dev/mmcblk0
                if 'mmcblk' in root_device:
                    result['boot_device'] = 'sdcard'
                    result['is_fallback'] = False  # SD card is primary if no SSD
                elif 'sda' in root_device or 'sdb' in root_device:
                    result['boot_device'] = 'ssd'
                    result['is_fallback'] = False
                else:
                    result['boot_device'] = 'unknown'
            else:
                result['error'] = "Could not determine root device"
                
        except (FileNotFoundError, PermissionError, IOError) as e:
            result['error'] = f"Cannot read /proc/cmdline: {e}"
        except Exception as e:
            result['error'] = f"Detection error: {e}"
    else:
        result['error'] = f"Unsupported platform: {system}"
    
    return result


def check_storage_health(storage_path):
    """
    Check if storage path is accessible and writable.
    
    Args:
        storage_path (Path): Path to check
    
    Returns:
        dict: {
            'accessible': bool,
            'writable': bool,
            'error': str or None
        }
    """
    import os
    from pathlib import Path
    
    result = {
        'accessible': False,
        'writable': False,
        'error': None
    }
    
    path = Path(storage_path)
    
    # Check existence
    if not path.exists():
        result['error'] = f"Path does not exist: {path}"
        return result
    
    result['accessible'] = True
    
    # Check writability
    try:
        test_file = path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        result['writable'] = True
    except Exception as e:
        result['error'] = f"Path not writable: {e}"
    
    return result


# ============================================================================
# SECTION 16: VALIDATION AND UTILITIES
# ============================================================================

def validate_paths():
    """
    Validate that all required paths exist and are accessible.
    Creates missing directories if possible.
    
    Returns:
        tuple: (success: bool, errors: list of error messages)
    """
    errors = []
    
    # Check storage path
    storage_path = Path(VIDEO_STORAGE_PATH) if isinstance(VIDEO_STORAGE_PATH, str) else VIDEO_STORAGE_PATH
    
    if not storage_path.exists():
        errors.append(f"Video storage path does not exist: {storage_path}")
        return False, errors
    
    if not os.access(str(storage_path), os.W_OK):
        errors.append(f"Video storage path is not writable: {storage_path}")
    
    # Check and create required directories
    required_dirs = [
        VIDEO_DIR,
        RECORDINGS_DIR,
        THUMBNAIL_DIR,
        TEMP_DIR,
        DATABASE_DIR,
        BACKUP_DIR,
        LOGS_DIR,
    ]
    
    for directory in required_dirs:
        dir_path = Path(directory) if isinstance(directory, str) else directory
        
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")
    
    # Check video device (warning only)
    if isinstance(VIDEO_DEVICE, str):
        if not Path(VIDEO_DEVICE).exists():
            import warnings
            warnings.warn(f"Video device not found: {VIDEO_DEVICE}")
    
    # Check Vosk model (warning only)
    if ENABLE_VOICE_COMMANDS:
        vosk_path = Path(VOSK_MODEL_PATH) if isinstance(VOSK_MODEL_PATH, str) else VOSK_MODEL_PATH
        if not vosk_path.exists():
            import warnings
            warnings.warn(f"Vosk model not found: {vosk_path}")
    
    return len(errors) == 0, errors


def get_config_summary():
    """
    Get a summary of current configuration for logging/debugging.
    
    Returns:
        dict: Dictionary containing key configuration values
    """
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "video_device": str(VIDEO_DEVICE),
        "video_resolution": f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
        "video_fps": VIDEO_FPS,
        "video_bitrate": VIDEO_BITRATE,
        "storage_path": str(VIDEO_STORAGE_PATH),
        "recordings_dir": str(RECORDINGS_DIR),
        "database_path": str(DATABASE_PATH),
        "voice_enabled": ENABLE_VOICE_COMMANDS,
        "debug_mode": DEBUG_MODE,
    }


def get_platform_info():
    """
    Legacy function for backward compatibility.
    Returns basic platform information without configuration values.
    
    Returns:
        dict: Platform information dictionary
    """
    import platform
    
    is_pi = False
    if platform.system() == 'Linux':
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                is_pi = 'Raspberry Pi' in model
        except:
            pass
    
    return {
        'system': platform.system(),
        'machine': platform.machine(),
        'python_version': platform.python_version(),
        'is_windows': platform.system() == 'Windows',
        'is_linux': platform.system() == 'Linux',
        'is_raspberry_pi': is_pi
    }


# ============================================================================
# SECTION 17: CONFIGURATION NOTES
# ============================================================================
#
# SWITCHING BETWEEN LAPTOP (WINDOWS) AND RASPBERRY PI (LINUX):
#
# AUTO-DETECTION MODE (FORCE_MANUAL_CONFIG = False):
#   - Copy the application to any platform
#   - Run without any configuration changes
#   - Settings auto-optimize for Windows or Pi
#
# MANUAL OVERRIDE MODE (FORCE_MANUAL_CONFIG = True):
#   1. Set FORCE_MANUAL_CONFIG = True at top of this file
#   2. Uncomment desired values in SECTION 3
#   3. Modify values as needed
#   4. Save and run
#
# NEW IN v1.1.0:
#   - Platform auto-detection (Windows vs Raspberry Pi)
#   - Manual override section for custom configurations
#   - Automatic encoder selection (OpenCV for Windows, FFmpeg for Pi)
#   - Automatic storage path selection
#
# ============================================================================


# ============================================================================
# SECTION 18: MODULE INITIALIZATION
# ============================================================================
# Validate paths on import to catch configuration errors early
if __name__ != "__main__":
    _valid, _errors = validate_paths()
    if not _valid and not DEBUG_MODE:
        import warnings
        for error in _errors:
            warnings.warn(f"Configuration warning: {error}")


# ============================================================================
# SECTION 19: MAIN EXECUTION (for testing configuration)
# ============================================================================
if __name__ == "__main__":
    """
    Test configuration by running this file directly.
    
    Usage:
        python config/app_config.py
    """
    print("=" * 60)
    print(f"{APP_NAME} v{APP_VERSION}")
    print("Configuration Validation")
    print("=" * 60)
    print()
    
    print("Validating paths...")
    valid, errors = validate_paths()
    
    if valid:
        print("✓ All paths are valid")
    else:
        print("✗ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("Please fix these errors before running the application.")
    
    print()
    print("Configuration Summary:")
    print("-" * 60)
    
    config = get_config_summary()
    for key, value in config.items():
        print(f"{key:20s}: {value}")
    
    print("-" * 60)
    print()
    print("Platform Information:")
    print("-" * 60)
    
    platform_info = get_platform_info()
    for key, value in platform_info.items():
        print(f"{key:20s}: {value}")
    
    print("-" * 60)
    print()
    print(f"Configuration Mode: {'MANUAL OVERRIDE' if FORCE_MANUAL_CONFIG else 'AUTO-DETECTION'}")
    print(f"Platform Detected: {_platform_config['platform_name']}")
    print("-" * 60)

    # Storage device detection test
    print()
    print("Storage Device Detection:")
    print("-" * 60)
    
    boot_info = detect_boot_device()
    print(f"Boot Device: {boot_info['boot_device']}")
    print(f"Boot Path: {boot_info['boot_path']}")
    print(f"Fallback Mode: {boot_info['is_fallback']}")
    if boot_info['error']:
        print(f"Error: {boot_info['error']}")
    
    print()
    print("Storage Health Check:")
    storage_health = check_storage_health(VIDEO_STORAGE_PATH)
    print(f"Accessible: {storage_health['accessible']}")
    print(f"Writable: {storage_health['writable']}")
    if storage_health['error']:
        print(f"Error: {storage_health['error']}")


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: VIRTUAL KEYBOARD TIMING
# ═══════════════════════════════════════════════════════════════════════════════
KEYBOARD_IDLE_HIDE_SECONDS = 5     # stage 1: hide keyboard after idle
KEYBOARD_KILL_SECONDS      = 120   # stage 2: free keyboard memory


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: GLOBAL UI FONT SETTINGS
# Applied via app.setFont() in main.py — affects ALL widgets that do not have
# an explicit font set. This includes:
#   - QMessageBox (system popups — Exit, warnings, errors)
#   - QComboBox dropdowns (where no explicit font is set)
#   - QLabel (where no explicit font is set)
#   - QDialog default text
#   - QPushButton (where no explicit font is set)
#
# Widgets with explicit setFont() calls are NOT affected (recording screen,
# top bar, nav bar, metadata dialog — these have their own font settings).
#
# To change global font: modify values below, restart app.
# ═══════════════════════════════════════════════════════════════════════════════
GLOBAL_UI_FONT_FAMILY = "Arial"
GLOBAL_UI_FONT_SIZE   = 16        # affects all widgets without explicit font


# ── QMessageBox appearance ────────────────────────────────────────────────────
# Controls all system popup dialogs (Exit, warnings, errors).
# Tweak these values to adjust size/font without touching code.
MSGBOX_FONT_SIZE    = 22    # popup message text size
MSGBOX_BTN_FONT     = 20    # button label font size
MSGBOX_BTN_WIDTH    = 160   # button minimum width px
MSGBOX_BTN_HEIGHT   = 60    # button minimum height px
MSGBOX_MSG_FONT     = 18    # message body text size


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: ON-SCREEN KEYBOARD DIMENSIONS
# Single source of truth for keyboard height used across all screens.
#
# MEASURED actual rendered height of one keyboard panel:
#   6(top margin) + 5 rows x 45(KEY_H) + 4 gaps x 4(GAP) + 6(bottom margin)
#   = 6 + 225 + 16 + 6 = 253px
#   Rounded up to 260px to match metadata_dialog confirmed working value.
#
# ONSCREEN_KB_Y = SCREEN_HEIGHT(600) - ONSCREEN_KB_HEIGHT(260) = 340
# ═══════════════════════════════════════════════════════════════════════════════
ONSCREEN_KB_HEIGHT = 253    # actual rendered height of one keyboard panel
ONSCREEN_KB_Y      = 347    # y position for bottom-anchored placement


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: LIBRARY SCREEN CONSTANTS
# Controls fonts, sizes and layout of the Library screen.
# Modify values here — no code changes needed.
# ═══════════════════════════════════════════════════════════════════════════════

# Search bar
LIB_SEARCH_FONT      = 22    # search field font size
LIB_SEARCH_HEIGHT    = 55    # search field height px
LIB_SEARCH_BTN_W     = 200   # Search button width px
LIB_SEARCH_BTN_H     = 55    # Search button height px
LIB_SEARCH_BTN_FONT  = 18    # Search button font size
LIB_KB_BTN_SIZE      = 90    # keyboard toggle button size px
LIB_LABEL_FONT       = 16    # Search/Found labels font size

# Table
LIB_TABLE_FONT       = 17    # table cell font size
LIB_TABLE_ROW_H      = 52    # table row height px
LIB_TABLE_HDR_FONT   = 17    # column header font size
LIB_SCROLLBAR_W      = 45    # scrollbar width px — wide for touch

# Buttons (single row at bottom)
LIB_BTN_H            = 60    # button height px
LIB_BTN_FONT         = 16    # button font size

# Library screen title row
LIB_TITLE_FONT       = 20     # "Video Library" font size
LIB_COUNT_FONT       = 14     # "Found: 109" font size
LIB_COUNT_COLOR      = '#555555'   # count label colour
LIB_SELECT_FONT      = 14     # "Selected: 3" font size
LIB_SELECT_COLOR     = '#1a3fa0'   # selection label colour

# ── Library screen checkbox ──────────────────────────────────────────────────
LIB_CHECKBOX_SIZE    = 36     # touch indicator size px — fits in LIB_TABLE_ROW_H(52)
