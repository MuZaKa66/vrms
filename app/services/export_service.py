"""
File: app/services/export_service.py

Module Description:
    USB export service for video files.
    
    Handles multi-file export with progress tracking and verification.

Dependencies:
    - shutil: File operations
    - pathlib: Path handling

Author: OT Video Dev Team
Date: January 30, 2026
Version: 1.0.0
"""

from typing import Tuple, Optional, List
from pathlib import Path
import shutil
import time

from app.utils.logger import AppLogger
from app.utils.file_utils import ensure_directory, get_file_size, copy_file
from app.utils.decorators import log_errors

logger = AppLogger("ExportService")


class ExportService:
    """
    USB export service.
    
    Methods:
        detect_usb_devices(): Find USB drives
        export_files(files, destination): Export multiple files
        verify_export(source, destination): Verify exported file
    
    Example:
        >>> export = ExportService()
        >>> 
        >>> # Detect USB
        >>> success, devices, error = export.detect_usb_devices()
        >>> 
        >>> # Export files
        >>> files = ["video1.mp4", "video2.mp4"]
        >>> success, count, error = export.export_files(files, "/media/usb0")
    """
    
    @log_errors
    def detect_usb_devices(self) -> Tuple[bool, List[str], Optional[str]]:
        """
        Detect connected USB storage devices.
        
        Returns:
            tuple: (success, device_paths, error_message)
        """
        try:
            devices = []
            media_path = Path("/media")
            
            if media_path.exists():
                for device_dir in media_path.iterdir():
                    if device_dir.is_dir():
                        devices.append(str(device_dir))
            
            if not devices:
                return True, [], "No USB devices detected. Please insert USB drive."
            
            logger.info(f"Found {len(devices)} USB device(s)")
            return True, devices, None
        
        except Exception as e:
            logger.error(f"USB detection error: {e}")
            return False, [], "Could not detect USB devices"
    
    @log_errors
    def export_files(self, source_files: List[str], destination: str) -> Tuple[bool, int, Optional[str]]:
        """
        Export multiple files to destination.
        
        Args:
            source_files: List of source file paths
            destination: Destination directory
        
        Returns:
            tuple: (success, files_exported, error_message)
        """
        try:
            destination = Path(destination)
            
            if not destination.exists():
                return False, 0, "Destination not found. USB may be disconnected."
            
            # Create export directory
            export_dir = destination / "OT_Videos"
            ensure_directory(export_dir)
            
            files_exported = 0
            
            for source_path in source_files:
                source = Path(source_path)
                
                if not source.exists():
                    logger.warning(f"Source file not found: {source_path}")
                    continue
                
                # Copy file
                dest_path = export_dir / source.name
                
                try:
                    shutil.copy2(str(source), str(dest_path))
                    files_exported += 1
                    logger.info(f"Exported: {source.name}")
                except Exception as e:
                    logger.error(f"Export failed for {source.name}: {e}")
            
            if files_exported == 0:
                return False, 0, "No files were exported"
            
            logger.info(f"Export complete: {files_exported} files")
            return True, files_exported, None
        
        except Exception as e:
            logger.error(f"Export error: {e}")
            return False, 0, "Export failed. USB may have disconnected."
    
    @log_errors
    def verify_export(self, source_path: str, dest_path: str) -> Tuple[bool, None, Optional[str]]:
        """
        Verify exported file matches source.
        
        Args:
            source_path: Original file path
            dest_path: Exported file path
        
        Returns:
            tuple: (success, None, error_message)
        """
        try:
            source = Path(source_path)
            dest = Path(dest_path)
            
            if not dest.exists():
                return False, None, "Exported file not found"
            
            # Compare file sizes
            source_size = get_file_size(source)
            dest_size = get_file_size(dest)
            
            if source_size != dest_size:
                return False, None, f"File size mismatch: {source_size} vs {dest_size}"
            
            logger.debug(f"Export verified: {dest.name}")
            return True, None, None
        
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False, None, "Could not verify export"


__all__ = ['ExportService']