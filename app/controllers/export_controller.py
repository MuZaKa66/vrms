"""
File: app/controllers/export_controller.py

Module Description:
    Export workflow controller.
    
    Manages USB export process:
    - Detect USB devices
    - Select recordings to export
    - Export with progress tracking
    - Verify exported files
    - Professional status messages

Author: OT Video Dev Team
Date: January 30, 2026
"""

from typing import Tuple, Optional, List
from pathlib import Path

from app.models.recording import Recording
from app.models.export_job import ExportJob, ExportStatus
from app.services.export_service import ExportService
from app.services.database_service import DatabaseService
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors

logger = AppLogger("ExportController")


class ExportController:
    """
    Export workflow controller.
    
    Methods:
        detect_usb(): Detect USB devices
        create_export_job(recording_ids, destination): Create export
        start_export(job): Begin export process
        get_export_status(job): Get progress
    
    Example:
        >>> controller = ExportController()
        >>> 
        >>> # Detect USB
        >>> success, devices, error = controller.detect_usb()
        >>> if devices:
        ...     device = devices[0]
        >>> 
        >>> # Create export job
        >>> recording_ids = [1, 2, 3]
        >>> success, job, error = controller.create_export_job(
        ...     recording_ids, device
        ... )
        >>> 
        >>> # Start export
        >>> success, _, error = controller.start_export(job)
        >>> 
        >>> # Monitor progress
        >>> status = controller.get_export_status(job)
        >>> print(status['message'])
    """
    
    def __init__(self):
        self.export_service = ExportService()
        self.database = DatabaseService()
        logger.info("Export controller initialized")
    
    @log_errors
    def detect_usb(self) -> Tuple[bool, List[str], Optional[str]]:
        """
        Detect USB storage devices.
        
        Returns:
            tuple: (success, device_paths, error_message)
        """
        return self.export_service.detect_usb_devices()
    
    @log_errors
    def create_export_job(self, recording_ids: List[int],
                         destination: str) -> Tuple[bool, Optional[ExportJob], Optional[str]]:
        """
        Create export job.
        
        Args:
            recording_ids: List of recording IDs to export
            destination: USB device path
        
        Returns:
            tuple: (success, export_job, error_message)
        """
        try:
            # Validate destination
            if not Path(destination).exists():
                return False, None, "USB device not found. Please insert USB drive."
            
            # Create job
            job = ExportJob.create_new(recording_ids, destination)
            
            logger.info(f"Created export job: {len(recording_ids)} recordings")
            return True, job, None
            
        except Exception as e:
            logger.error(f"Error creating export job: {e}")
            return False, None, "Could not create export job"
    
    @log_errors
    def start_export(self, job: ExportJob) -> Tuple[bool, None, Optional[str]]:
        """
        Start export process.
        
        Args:
            job: Export job to execute
        
        Returns:
            tuple: (success, None, error_message)
        """
        try:
            # Mark as started
            job.start()
            
            # Get recordings
            source_files = []
            for rec_id in job.recording_ids:
                success, recording, error = self.database.get_recording(rec_id)
                if success and recording.filepath:
                    source_files.append(recording.filepath)
            
            if not source_files:
                job.mark_failed("No valid recordings to export")
                return False, None, "No recordings found"
            
            # Export files
            success, count, error = self.export_service.export_files(
                source_files,
                job.destination
            )
            
            if not success:
                job.mark_failed(error)
                return False, None, error
            
            # Mark complete
            job.mark_completed()
            
            logger.info(f"Export completed: {count} files")
            return True, None, None
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            job.mark_failed(str(e))
            return False, None, "Export failed"
    
    def get_export_status(self, job: ExportJob) -> dict:
        """Get export job status."""
        return job.get_detailed_status()


__all__ = ['ExportController']
