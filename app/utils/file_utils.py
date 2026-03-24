"""
File: app/utils/file_utils.py

Module Description:
    File system utilities for the OT Video Management System.
    
    Provides helper functions for:
    - Directory operations (create, check, clean)
    - File operations (copy, move, delete, size)
    - Storage space monitoring
    - Filename generation
    - Path validation
    
    All functions handle errors gracefully and log issues.

Dependencies:
    - os, shutil: File system operations
    - pathlib: Modern path handling
    - datetime: For timestamps in filenames

Usage Example:
    >>> from app.utils.file_utils import ensure_directory, get_free_space_gb
    >>> ensure_directory("videostore/videos")
    >>> free_space = get_free_space_gb("videostore")
    >>> print(f"Free space: {free_space} GB")

Author: OT Video Dev Team
Date: January 28, 2026
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Union

from app.utils.logger import AppLogger
from app.utils.constants import KB, MB, GB


# Initialize module logger
logger = AppLogger("FileUtils")


# ============================================================================
# DIRECTORY OPERATIONS
# ============================================================================
def ensure_directory(path: Union[str, Path]) -> bool:
    """
    Create directory if it doesn't exist.
    
    Creates parent directories as needed (equivalent to mkdir -p).
    Safe to call multiple times - does nothing if directory exists.
    
    Args:
        path: Directory path to create
    
    Returns:
        bool: True if directory exists (created or already existed), False on error
    
    Example:
        >>> ensure_directory("videostore/videos/2026/01")
        True
    """
    try:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {path}")
        return True
        
    except PermissionError:
        logger.error(f"Permission denied creating directory: {path}")
        return False
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False


def directory_exists(path: Union[str, Path]) -> bool:
    """
    Check if directory exists.
    
    Args:
        path: Directory path to check
    
    Returns:
        bool: True if directory exists, False otherwise
    """
    return Path(path).is_dir()


def is_empty_directory(path: Union[str, Path]) -> bool:
    """
    Check if directory is empty.
    
    Args:
        path: Directory path to check
    
    Returns:
        bool: True if directory is empty, False if contains files/dirs
    """
    try:
        path = Path(path)
        if not path.is_dir():
            return False
        return len(list(path.iterdir())) == 0
    except Exception:
        return False


def clean_directory(path: Union[str, Path], recursive: bool = False) -> bool:
    """
    Remove all contents of directory (but keep directory itself).
    
    Args:
        path: Directory to clean
        recursive: If True, removes subdirectories too
    
    Returns:
        bool: True if successful, False on error
    """
    try:
        path = Path(path)
        
        if not path.is_dir():
            logger.warning(f"Not a directory: {path}")
            return False
        
        for item in path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    logger.debug(f"Deleted file: {item}")
                elif item.is_dir() and recursive:
                    shutil.rmtree(item)
                    logger.debug(f"Deleted directory: {item}")
            except Exception as e:
                logger.error(f"Error deleting {item}: {e}")
        
        logger.info(f"Cleaned directory: {path}")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning directory {path}: {e}")
        return False


# ============================================================================
# FILE OPERATIONS
# ============================================================================
def file_exists(path: Union[str, Path]) -> bool:
    """Check if file exists."""
    return Path(path).is_file()


def get_file_size(path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        path: File path
    
    Returns:
        int: File size in bytes, 0 if file doesn't exist or error
    """
    try:
        return Path(path).stat().st_size
    except Exception as e:
        logger.error(f"Error getting file size for {path}: {e}")
        return 0


def get_file_size_human(path: Union[str, Path]) -> str:
    """
    Get file size in human-readable format.
    
    Returns:
        str: Human-readable size (e.g., "1.5 MB", "300 KB", "2.3 GB")
    """
    size_bytes = get_file_size(path)
    
    if size_bytes < KB:
        return f"{size_bytes} B"
    elif size_bytes < MB:
        return f"{size_bytes / KB:.1f} KB"
    elif size_bytes < GB:
        return f"{size_bytes / MB:.1f} MB"
    else:
        return f"{size_bytes / GB:.2f} GB"


def safe_delete(path: Union[str, Path], secure: bool = False) -> bool:
    """
    Safely delete a file with error handling.
    
    Args:
        path: File to delete
        secure: If True, overwrite file before deletion (slower but more secure)
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        path = Path(path)
        
        if not path.exists():
            logger.warning(f"File doesn't exist: {path}")
            return False
        
        # Secure deletion: overwrite file first
        if secure and path.is_file():
            file_size = path.stat().st_size
            with open(path, 'wb') as f:
                import random
                f.write(bytes([random.randint(0, 255) for _ in range(file_size)]))
            logger.debug(f"File overwritten before deletion: {path}")
        
        # Delete file or directory
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        
        logger.info(f"Deleted: {path}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting {path}: {e}")
        return False


def copy_file(source: Union[str, Path], destination: Union[str, Path], 
              overwrite: bool = False) -> bool:
    """
    Copy file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        overwrite: If True, overwrite destination if it exists
    
    Returns:
        bool: True if copied successfully, False otherwise
    """
    try:
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            logger.error(f"Source file doesn't exist: {source}")
            return False
        
        if destination.exists() and not overwrite:
            logger.error(f"Destination exists and overwrite=False: {destination}")
            return False
        
        # Ensure destination directory exists
        ensure_directory(destination.parent)
        
        # Copy file
        shutil.copy2(source, destination)
        logger.info(f"Copied: {source} -> {destination}")
        return True
        
    except Exception as e:
        logger.error(f"Error copying {source} to {destination}: {e}")
        return False


def move_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
    """
    Move file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
    
    Returns:
        bool: True if moved successfully, False otherwise
    """
    try:
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            logger.error(f"Source file doesn't exist: {source}")
            return False
        
        # Ensure destination directory exists
        ensure_directory(destination.parent)
        
        # Move file
        shutil.move(str(source), str(destination))
        logger.info(f"Moved: {source} -> {destination}")
        return True
        
    except Exception as e:
        logger.error(f"Error moving {source} to {destination}: {e}")
        return False


# ============================================================================
# STORAGE OPERATIONS
# ============================================================================
def get_free_space(path: Union[str, Path]) -> int:
    """
    Get free space in bytes. Works on both Windows and Linux.
    
    Args:
        path: Path to check (can be file or directory)
    
    Returns:
        int: Free space in bytes, 0 on error
    """
    try:
        # shutil.disk_usage works on both Windows and Linux
        stat = shutil.disk_usage(str(path))
        return stat.free
    except Exception as e:
        logger.error(f"Error getting free space for {path}: {e}")
        return 0


def get_free_space_gb(path: Union[str, Path]) -> float:
    """
    Get free space in gigabytes. Works on both Windows and Linux.
    
    Args:
        path: Path to check
    
    Returns:
        float: Free space in GB, 0.0 on error
    """
    try:
        free_bytes = get_free_space(path)
        return free_bytes / GB
    except Exception as e:
        logger.error(f"Error getting free space GB for {path}: {e}")
        return 0.0


def get_total_space_gb(path: Union[str, Path]) -> float:
    """
    Get total space in gigabytes. Works on both Windows and Linux.
    
    Args:
        path: Path to check
    
    Returns:
        float: Total space in GB, 0.0 on error
    """
    try:
        stat = shutil.disk_usage(str(path))
        return stat.total / GB
    except Exception as e:
        logger.error(f"Error getting total space for {path}: {e}")
        return 0.0


def get_used_space_gb(path: Union[str, Path]) -> float:
    """
    Get used space in gigabytes. Works on both Windows and Linux.
    
    Args:
        path: Path to check
    
    Returns:
        float: Used space in GB, 0.0 on error
    """
    try:
        stat = shutil.disk_usage(str(path))
        return stat.used / GB
    except Exception as e:
        logger.error(f"Error getting used space for {path}: {e}")
        return 0.0


# ============================================================================
# FILENAME OPERATIONS
# ============================================================================
def generate_filename(prefix: str = "recording", extension: str = ".mp4", 
                     sequence: Optional[int] = None) -> str:
    """
    Generate timestamped filename.
    
    Format: YYYYMMDD_HHMMSS_NNN.ext
    Example: 20260128_143022_001.mp4
    
    Args:
        prefix: Filename prefix (default: "recording")
        extension: File extension (default: ".mp4")
        sequence: Optional sequence number
    
    Returns:
        str: Generated filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if sequence is None:
        sequence = 1
    
    sequence_str = f"{sequence:03d}"
    
    if not extension.startswith('.'):
        extension = '.' + extension
    
    filename = f"{timestamp}_{sequence_str}{extension}"
    
    logger.debug(f"Generated filename: {filename}")
    return filename


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    Safe for both Linux and Windows filesystems.
    
    Args:
        filename: Original filename
    
    Returns:
        str: Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        name = name[:255-len(ext)]
        filename = name + ext
    
    return filename


# ============================================================================
# EXPORT
# ============================================================================
__all__ = [
    # Directory operations
    'ensure_directory',
    'directory_exists',
    'is_empty_directory',
    'clean_directory',
    
    # File operations
    'file_exists',
    'get_file_size',
    'get_file_size_human',
    'safe_delete',
    'copy_file',
    'move_file',
    
    # Storage operations
    'get_free_space',
    'get_free_space_gb',
    'get_total_space_gb',
    'get_used_space_gb',
    
    # Filename operations
    'generate_filename',
    'sanitize_filename',
]
