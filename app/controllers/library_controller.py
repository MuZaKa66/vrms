"""
File: app/controllers/library_controller.py

Module Description:
    Video library management controller.
    
    Handles:
    - Get all recordings
    - Search/filter recordings
    - Sort recordings
    - Delete recordings
    - Load thumbnails

Author: OT Video Dev Team
Date: January 30, 2026
"""

from typing import Tuple, Optional, List
from pathlib import Path

from app.models.recording import Recording
from app.services.database_service import DatabaseService
from app.services.storage_service import StorageService
from app.services.thumbnail_service import ThumbnailService
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors

logger = AppLogger("LibraryController")


class LibraryController:
    """
    Video library management controller.
    
    Methods:
        get_all_recordings(limit): Get recent recordings
        search_recordings(**filters): Search by criteria
        delete_recording(recording_id): Delete recording
        generate_thumbnail(recording): Create thumbnail
    
    Example:
        >>> controller = LibraryController()
        >>> 
        >>> # Get recent recordings
        >>> success, recordings, error = controller.get_all_recordings(limit=20)
        >>> 
        >>> # Search by patient
        >>> success, results, error = controller.search_recordings(
        ...     patient_name="John"
        ... )
        >>> 
        >>> # Delete recording
        >>> success, _, error = controller.delete_recording(recording_id=1)
    """
    
    def __init__(self):
        self.database = DatabaseService()
        self.storage = StorageService()
        self.thumbnail = ThumbnailService()
        logger.info("Library controller initialized")
    
    @log_errors
    def get_all_recordings(self, limit: Optional[int] = None,
                          order_by: str = "created_timestamp DESC") -> Tuple[bool, List[Recording], Optional[str]]:
        """
        Get all recordings from library.
        
        Args:
            limit: Maximum number to return
            order_by: Sort order (default: newest first)
        
        Returns:
            tuple: (success, list_of_recordings, error_message)
        """
        success, recordings, error = self.database.get_all_recordings(
            order_by=order_by,
            limit=limit
        )
        
        if not success:
            return False, [], error
        
        logger.info(f"Retrieved {len(recordings)} recordings")
        return True, recordings, None
    
    @log_errors
    def search_recordings(self,
                         patient_name: Optional[str] = None,
                         procedure_name: Optional[str] = None,
                         operating_theatre: Optional[str] = None,
                         surgeon_name: Optional[str] = None,
                         date_from: Optional[str] = None,
                         date_to: Optional[str] = None) -> Tuple[bool, List[Recording], Optional[str]]:
        """
        Search recordings by criteria.
        
        All parameters optional. Combines with AND logic.
        
        Returns:
            tuple: (success, matching_recordings, error_message)
        """
        success, recordings, error = self.database.search_recordings(
            patient_name=patient_name,
            procedure_name=procedure_name,
            operating_theatre=operating_theatre,
            surgeon_name=surgeon_name,
            date_from=date_from,
            date_to=date_to
        )
        
        if not success:
            return False, [], error
        
        logger.info(f"Search returned {len(recordings)} results")
        return True, recordings, None
    
    @log_errors
    def delete_recording(self, recording_id: int,
                        delete_file: bool = True) -> Tuple[bool, None, Optional[str]]:
        """
        Delete recording from library.
        
        Args:
            recording_id: Database ID
            delete_file: Also delete video file (default: True)
        
        Returns:
            tuple: (success, None, error_message)
        """
        try:
            # Get recording first
            success, recording, error = self.database.get_recording(recording_id)
            if not success:
                return False, None, error
            
            # Delete video file
            if delete_file and recording.filepath:
                self.storage.delete_recording_file(recording.filepath)
            
            # Delete from database
            success, _, error = self.database.delete_recording(recording_id)
            if not success:
                return False, None, error
            
            logger.info(f"Deleted recording: {recording_id}")
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error deleting recording: {e}")
            return False, None, "Could not delete recording"
    
    @log_errors
    def generate_thumbnail(self, recording: Recording) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate thumbnail for recording.
        
        Args:
            recording: Recording object
        
        Returns:
            tuple: (success, thumbnail_path, error_message)
        """
        if not recording.filepath or not Path(recording.filepath).exists():
            return False, None, "Video file not found"
        
        # Generate thumbnail path
        thumb_filename = f"{Path(recording.filename).stem}.jpg"
        thumb_path = Path("/mnt/videostore/thumbnails") / thumb_filename
        
        # Generate thumbnail
        success, path, error = self.thumbnail.generate_thumbnail(
            recording.filepath,
            str(thumb_path)
        )
        
        if not success:
            return False, None, error
        
        # Update recording
        recording.thumbnail_path = path
        self.database.update_recording(recording)
        
        return True, path, None


__all__ = ['LibraryController']