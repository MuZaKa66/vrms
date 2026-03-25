"""
File: app/services/storage_service.py

Module Description:
    Storage management service for the OT Video Management System.
    
    Provides professional file system operations:
    - Storage space monitoring with warnings
    - Directory management (auto-create)
    - File operations (save, delete, move)
    - Video file organization by date
    - Storage health checks
    - Professional error messages
    - Protection for active recording temp files

Design Philosophy:
    - Never crash on storage errors
    - Always provide user-friendly error messages
    - Auto-create missing directories
    - Validate before executing operations
    - Complete audit trail in logs
    - Never delete files currently in use

Dependencies:
    - pathlib: Modern path handling
    - shutil: File operations
    - os: System operations
    - app.utils: File utilities and logging

Usage Example:
    >>> from app.services.storage_service import StorageService
    >>> 
    >>> storage = StorageService()
    >>> 
    >>> # Check space before recording
    >>> success, free_gb, error = storage.get_free_space_gb()
    >>> if free_gb < 10:
    ...     print("Warning: Low storage!")
    >>> 
    >>> # Check if can record
    >>> success, can_record, error = storage.can_record(30)
    >>> if not can_record:
    ...     display_error(error)
    >>> 
    >>> # Save recording
    >>> success, final_path, error = storage.save_recording(
    ...     temp_path="/tmp/recording.mp4",
    ...     recording=recording_object
    ... )

Author: OT Video Dev Team
Date: March 25, 2026
Version: 1.0.1
Changelog:
    - v1.0.1: Added protection for active recording temp files during cleanup
    - v1.0.0: Initial release
"""

# ============================================================================
# IMPORTS
# ============================================================================
from pathlib import Path
from typing import Tuple, Optional, Dict
import shutil
import os

from config.app_config import (
    VIDEO_STORAGE_PATH,
    VIDEO_DIR,
    THUMBNAIL_DIR,
    TEMP_DIR,
    DATABASE_DIR,
    BACKUP_DIR,
    STORAGE_WARNING_THRESHOLD_GB,
    STORAGE_CRITICAL_THRESHOLD_GB
)
from app.models.recording import Recording
from app.utils.logger import AppLogger
from app.utils.file_utils import (
    ensure_directory,
    get_free_space_gb,
    get_total_space_gb,
    get_used_space_gb,
    get_file_size,
    safe_delete,
    copy_file,
    move_file
)
from app.utils.decorators import log_errors, retry

# Initialize logger
logger = AppLogger("StorageService")


# ============================================================================
# STORAGE SERVICE CLASS
# ============================================================================
class StorageService:
    """
    Storage management service.
    
    Provides safe, professional storage operations with:
    - Automatic directory creation
    - Storage space monitoring
    - File organization by date
    - Error recovery
    - User-friendly error messages
    - Protection for active recording temp files
    
    All operations return (success, data, error_message) tuples.
    
    Attributes:
        storage_path (Path): Main storage directory (/mnt/videostore)
        video_dir (Path): Video files directory
        thumbnail_dir (Path): Thumbnail images directory
        temp_dir (Path): Temporary files directory
    
    Methods:
        # Storage monitoring
        get_free_space_gb(): Get free space in GB
        get_storage_status(): Get detailed storage status
        is_storage_low(): Check if storage running low
        can_record(duration): Check if enough space for recording
        
        # File operations
        save_recording(temp_path, recording): Save video to permanent storage
        delete_recording_file(filepath): Delete video file
        get_recording_file_size(filepath): Get file size
        
        # Directory management
        ensure_directories(): Create required directories
        clean_temp_directory(): Remove temporary files (protects active recordings)
    
    Example:
        >>> storage = StorageService()
        >>> 
        >>> # Check before recording
        >>> success, can_record, error = storage.can_record(30)
        >>> if not can_record:
        ...     print(f"Cannot record: {error}")
        >>> 
        >>> # Save recording after encoding
        >>> success, path, error = storage.save_recording(
        ...     temp_path="/tmp/recording.mp4",
        ...     recording=rec
        ... )
        >>> if success:
        ...     print(f"Saved to: {path}")
    """
    
    def __init__(self):
        """
        Initialize storage service.
        
        Creates required directories if they don't exist.
        Verifies storage is accessible.
        
        Example:
            >>> storage = StorageService()
            >>> # Automatically creates all required directories
        """
        self.storage_path = Path(VIDEO_STORAGE_PATH)
        self.video_dir = Path(VIDEO_DIR)
        self.thumbnail_dir = Path(THUMBNAIL_DIR)
        self.temp_dir = Path(TEMP_DIR)
        self.database_dir = Path(DATABASE_DIR)
        self.backup_dir = Path(BACKUP_DIR)
        
        # Ensure all directories exist on initialization
        success, error = self.ensure_directories()
        if not success:
            logger.error(f"Storage initialization failed: {error}")
        else:
            logger.info("Storage service initialized successfully")
    
    # ========================================================================
    # DIRECTORY MANAGEMENT
    # ========================================================================
    
    @log_errors
    def ensure_directories(self) -> Tuple[bool, Optional[str]]:
        """
        Ensure all required directories exist.
        
        Creates directories if they don't exist.
        Verifies write permissions.
        
        Returns:
            tuple: (success, error_message)
        
        Example:
            >>> success, error = storage.ensure_directories()
            >>> if not success:
            ...     print(f"Cannot access storage: {error}")
        """
        try:
            # List of required directories
            required_dirs = [
                self.storage_path,
                self.video_dir,
                self.thumbnail_dir,
                self.temp_dir,
                self.database_dir,
                self.backup_dir
            ]
            
            # Create each directory
            for directory in required_dirs:
                if not ensure_directory(directory):
                    return False, f"Cannot create directory: {directory}"
            
            # Verify storage path is writable
            if not os.access(self.storage_path, os.W_OK):
                return False, f"Storage is not writable: {self.storage_path}"
            
            logger.debug("All storage directories verified")
            return True, None
            
        except Exception as e:
            error_msg = f"Error creating directories: {e}"
            logger.error(error_msg)
            return False, "Cannot access storage. Please check USB/SSD connection."
    
    @log_errors
    def clean_temp_directory(self) -> Tuple[bool, int, Optional[str]]:
        """
        Clean temporary directory.
        
        Removes all files from temp directory EXCEPT those currently in use
        by active recordings. This prevents deletion of files being written.
        
        Use after recording is saved or on startup.
        
        Returns:
            tuple: (success, files_removed, error_message)
        
        Example:
            >>> success, count, error = storage.clean_temp_directory()
            >>> print(f"Removed {count} temporary files")
        """
        try:
            files_removed = 0
            active_files = []
            
            if not self.temp_dir.exists():
                return True, 0, None
            
            # ================================================================
            # PROTECT ACTIVE RECORDING FILES
            # ================================================================
            # Get list of files currently being written by active recordings
            # This prevents deletion of temp files that are still in use
            try:
                # Import RecordingController to get active temp file
                from app.controllers.recording_controller import RecordingController
                active_file = RecordingController.get_active_temp_file()
                if active_file:
                    active_files.append(str(active_file))
                    logger.debug(f"Active recording file protected: {active_file}")
            except ImportError:
                # Recording controller not available - no protection needed
                pass
            except AttributeError:
                # Function doesn't exist in recording controller
                logger.debug("get_active_temp_file not available in RecordingController")
            except Exception as e:
                # Log warning but continue with cleanup
                logger.warning(f"Could not check active recordings: {e}")
            
            # ================================================================
            # CLEANUP LOOP - Skip active files
            # ================================================================
            for item in self.temp_dir.iterdir():
                if item.is_file():
                    # Skip if this file is currently in use by active recording
                    if str(item) in active_files:
                        logger.debug(f"Skipping active file: {item.name}")
                        continue
                    
                    try:
                        item.unlink()
                        files_removed += 1
                        logger.debug(f"Removed temp file: {item.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove {item.name}: {e}")
            
            logger.info(f"Cleaned temp directory: {files_removed} files removed")
            return True, files_removed, None
            
        except Exception as e:
            error_msg = f"Error cleaning temp directory: {e}"
            logger.error(error_msg)
            return False, 0, "Could not clean temporary files"
    
    # ========================================================================
    # STORAGE MONITORING
    # ========================================================================
    
    @log_errors
    def get_free_space_gb(self) -> Tuple[bool, float, Optional[str]]:
        """
        Get free space in gigabytes.
        
        Returns:
            tuple: (success, free_space_gb, error_message)
        
        Example:
            >>> success, free_gb, error = storage.get_free_space_gb()
            >>> if success:
            ...     print(f"{free_gb:.2f} GB free")
        """
        try:
            free_gb = get_free_space_gb(self.storage_path)
            return True, free_gb, None
            
        except Exception as e:
            error_msg = f"Error getting free space: {e}"
            logger.error(error_msg)
            return False, 0.0, "Cannot access storage information"
    
    @log_errors
    def get_storage_status(self) -> Tuple[bool, Dict, Optional[str]]:
        """
        Get detailed storage status.
        
        Returns:
            tuple: (success, status_dict, error_message)
                  status_dict contains:
                  - total_gb: Total storage capacity
                  - used_gb: Used storage
                  - free_gb: Free storage
                  - percent_used: Percentage used
                  - is_low: Below warning threshold
                  - is_critical: Below critical threshold
        
        Example:
            >>> success, status, error = storage.get_storage_status()
            >>> if status['is_low']:
            ...     print("Warning: Low storage!")
            >>> if status['is_critical']:
            ...     print("Critical: Cannot record!")
        """
        try:
            total_gb = get_total_space_gb(self.storage_path)
            used_gb = get_used_space_gb(self.storage_path)
            free_gb = get_free_space_gb(self.storage_path)
            
            percent_used = (used_gb / total_gb * 100) if total_gb > 0 else 0
            
            status = {
                'total_gb': total_gb,
                'used_gb': used_gb,
                'free_gb': free_gb,
                'percent_used': percent_used,
                'is_low': free_gb < STORAGE_WARNING_THRESHOLD_GB,
                'is_critical': free_gb < STORAGE_CRITICAL_THRESHOLD_GB,
                'warning_threshold_gb': STORAGE_WARNING_THRESHOLD_GB,
                'critical_threshold_gb': STORAGE_CRITICAL_THRESHOLD_GB
            }
            
            logger.debug(
                f"Storage status: {free_gb:.2f} GB free of {total_gb:.2f} GB "
                f"({percent_used:.1f}% used)"
            )
            
            return True, status, None
            
        except Exception as e:
            error_msg = f"Error getting storage status: {e}"
            logger.error(error_msg)
            return False, {}, "Cannot access storage information"
    
    @log_errors
    def is_storage_low(self) -> Tuple[bool, bool, Optional[str]]:
        """
        Check if storage is running low.
        
        Returns:
            tuple: (success, is_low, error_message)
                  is_low: True if below warning threshold
        
        Example:
            >>> success, is_low, error = storage.is_storage_low()
            >>> if is_low:
            ...     display_warning("Low storage space")
        """
        success, free_gb, error = self.get_free_space_gb()
        
        if not success:
            return False, False, error
        
        is_low = free_gb < STORAGE_WARNING_THRESHOLD_GB
        
        if is_low:
            logger.warning(f"Storage is low: {free_gb:.2f} GB remaining")
        
        return True, is_low, None
    
    @log_errors
    def can_record(self, estimated_duration_minutes: int = 60) -> Tuple[bool, bool, Optional[str]]:
        """
        Check if there's enough space to record.
        
        Estimates space needed based on duration and bitrate.
        Provides user-friendly error messages.
        
        Args:
            estimated_duration_minutes: Expected recording duration
        
        Returns:
            tuple: (success, can_record, error_message)
        
        Example:
            >>> success, can_record, error = storage.can_record(30)
            >>> if not can_record:
            ...     display_error(error)
            ...     # Error might be: "Not enough storage space. 
            ...     #                 Need 2.5 GB, have 1.2 GB free."
        """
        success, free_gb, error = self.get_free_space_gb()
        
        if not success:
            return False, False, error
        
        # Estimate space needed
        # 3 Mbps bitrate ≈ 0.375 MB/s ≈ 22.5 MB/minute ≈ 1.35 GB/hour
        # Add 20% buffer for safety
        estimated_gb = (estimated_duration_minutes / 60) * 1.35 * 1.2
        
        # Check if we have enough space + critical threshold
        required_gb = estimated_gb + STORAGE_CRITICAL_THRESHOLD_GB
        
        can_record = free_gb >= required_gb
        
        if not can_record:
            logger.warning(
                f"Insufficient space for recording: "
                f"need {required_gb:.2f} GB, have {free_gb:.2f} GB"
            )
            return True, False, (
                f"Not enough storage space. "
                f"Need {required_gb:.1f} GB, have {free_gb:.1f} GB free. "
                f"\n\nPlease delete old recordings or export videos to USB."
            )
        
        return True, True, None
    
    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================
    
    @log_errors
    @retry(max_attempts=3, delay=1.0)
    def save_recording(self, temp_path: str, recording: Recording) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Save recording from temporary location to permanent storage.
        
        Moves file from temp directory to organized storage by date.
        Creates year/month subdirectories automatically.
        Updates recording filepath.
        
        Args:
            temp_path: Path to temporary recording file
            recording: Recording object with metadata
        
        Returns:
            tuple: (success, final_path, error_message)
        
        Example:
            >>> success, path, error = storage.save_recording(
            ...     temp_path="/tmp/recording.mp4",
            ...     recording=rec
            ... )
            >>> if success:
            ...     print(f"Saved to: {path}")
            ...     # Path will be: /mnt/videostore/videos/2026/01/filename.mp4
        """
        try:
            # Extract year and month from recording date
            # Format: YYYY-MM-DD
            year, month, _ = recording.recording_date.split('-')
            
            # Create destination directory: /videos/YYYY/MM/
            dest_dir = self.video_dir / year / month
            
            if not ensure_directory(dest_dir):
                return False, None, f"Cannot create directory: {dest_dir}"
            
            # Build final path
            final_path = dest_dir / recording.filename
            
            # Verify temp file exists
            temp_path_obj = Path(temp_path)
            
            if not temp_path_obj.exists():
                return False, None, f"Temporary file not found: {temp_path}"
            
            # Get file size before moving
            file_size = get_file_size(temp_path)
            recording.file_size_bytes = file_size
            
            # Move file from temp to permanent storage
            try:
                shutil.move(str(temp_path_obj), str(final_path))
            except Exception as e:
                logger.error(f"Error moving file: {e}")
                return False, None, "Cannot save recording. Storage may be full."
            
            # Update recording filepath
            recording.filepath = str(final_path)
            
            logger.info(
                f"Saved recording: {recording.filename} "
                f"({file_size / (1024**2):.2f} MB)"
            )
            
            return True, str(final_path), None
            
        except Exception as e:
            error_msg = f"Error saving recording: {e}"
            logger.error(error_msg)
            return False, None, "Could not save recording. Please try again."
    
    @log_errors
    def delete_recording_file(self, filepath: str) -> Tuple[bool, None, Optional[str]]:
        """
        Delete recording video file.
        
        Args:
            filepath: Path to video file
        
        Returns:
            tuple: (success, None, error_message)
        
        Example:
            >>> success, _, error = storage.delete_recording_file(
            ...     "/mnt/videostore/videos/2026/01/video.mp4"
            ... )
            >>> if success:
            ...     print("File deleted successfully")
        """
        try:
            if not safe_delete(filepath):
                return False, None, f"File not found: {filepath}"
            
            logger.info(f"Deleted recording file: {filepath}")
            return True, None, None
            
        except Exception as e:
            error_msg = f"Error deleting file: {e}"
            logger.error(error_msg)
            return False, None, "Could not delete file. It may be in use."
    
    @log_errors
    def get_recording_file_size(self, filepath: str) -> Tuple[bool, int, Optional[str]]:
        """
        Get size of recording file.
        
        Args:
            filepath: Path to video file
        
        Returns:
            tuple: (success, size_bytes, error_message)
        
        Example:
            >>> success, size_bytes, error = storage.get_recording_file_size(path)
            >>> if success:
            ...     size_mb = size_bytes / (1024**2)
            ...     print(f"File size: {size_mb:.2f} MB")
        """
        try:
            size_bytes = get_file_size(filepath)
            
            if size_bytes == 0:
                return False, 0, f"File not found or empty: {filepath}"
            
            return True, size_bytes, None
            
        except Exception as e:
            error_msg = f"Error getting file size: {e}"
            logger.error(error_msg)
            return False, 0, "Could not access file"


# ============================================================================
# EXPORT
# ============================================================================
__all__ = [
    'StorageService',
]