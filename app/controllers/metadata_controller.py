"""
File: app/controllers/metadata_controller.py

Module Description:
    Metadata management controller.
    
    Handles all metadata operations:
    - Add/edit metadata for recordings
    - Validate metadata
    - Update filename when patient name added
    - Save to database
    - Metadata presets
    
    Zero-friction design - all metadata optional.

Author: OT Video Dev Team
Date: January 30, 2026
"""

from typing import Tuple, Optional
from app.models.recording import Recording
from app.models.metadata import RecordingMetadata, MetadataPresets, CommonProcedures
from app.services.database_service import DatabaseService
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors

logger = AppLogger("MetadataController")


class MetadataController:
    """
    Metadata management controller.
    
    Methods:
        add_metadata(recording, metadata): Add metadata to recording
        update_metadata(recording, metadata): Update existing metadata
        get_procedure_list(): Get common procedures
        apply_preset(recording, preset_name): Apply metadata preset
    
    Example:
        >>> from app.models.metadata import RecordingMetadata
        >>> 
        >>> controller = MetadataController()
        >>> 
        >>> # Add metadata after recording
        >>> metadata = RecordingMetadata(
        ...     patient_name="John Smith",
        ...     procedure="Cataract Surgery"
        ... )
        >>> 
        >>> success, updated_rec, error = controller.add_metadata(
        ...     recording, metadata
        ... )
    """
    
    def __init__(self):
        self.database = DatabaseService()
        logger.info("Metadata controller initialized")
    
    @log_errors
    def add_metadata(self, recording: Recording, 
                     metadata: RecordingMetadata) -> Tuple[bool, Optional[Recording], Optional[str]]:
        """
        Add metadata to recording.
        
        Updates recording with metadata and saves to database.
        Updates filename if patient name provided.
        
        Args:
            recording: Recording object
            metadata: Metadata to add
        
        Returns:
            tuple: (success, updated_recording, error_message)
        """
        try:
            # Validate metadata
            valid, errors = metadata.validate()
            if not valid:
                return False, None, f"Invalid metadata: {'; '.join(errors)}"
            
            # Sanitize metadata
            metadata.sanitize()
            
            # Apply to recording
            metadata.apply_to_recording(recording)
            
            # Update in database
            success, _, error = self.database.update_recording(recording)
            if not success:
                return False, None, error
            
            logger.info(f"Metadata added to {recording.filename}")
            return True, recording, None
            
        except Exception as e:
            logger.error(f"Error adding metadata: {e}")
            return False, None, "Could not save metadata"
    
    @log_errors
    def update_metadata(self, recording: Recording,
                       metadata: RecordingMetadata) -> Tuple[bool, Optional[Recording], Optional[str]]:
        """Update existing metadata."""
        return self.add_metadata(recording, metadata)
    
    def get_procedure_list(self) -> list:
        """Get list of common procedures."""
        return CommonProcedures.get_all_names()
    
    @log_errors
    def apply_preset(self, recording: Recording,
                    preset_name: str) -> Tuple[bool, Optional[Recording], Optional[str]]:
        """
        Apply metadata preset.
        
        Args:
            recording: Recording object
            preset_name: 'emergency', 'teaching', 'routine_cataract'
        
        Returns:
            tuple: (success, updated_recording, error_message)
        """
        try:
            # Get preset
            if preset_name == 'emergency':
                metadata = MetadataPresets.emergency_surgery()
            elif preset_name == 'teaching':
                metadata = MetadataPresets.teaching_case()
            elif preset_name == 'routine_cataract':
                metadata = MetadataPresets.routine_cataract()
            else:
                return False, None, f"Unknown preset: {preset_name}"
            
            # Apply preset
            return self.add_metadata(recording, metadata)
            
        except Exception as e:
            logger.error(f"Error applying preset: {e}")
            return False, None, "Could not apply preset"


__all__ = ['MetadataController']