"""
File: app/models/recording.py

Recording data model with zero-friction design.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple, List
from app.utils.datetime_utils import get_date, get_time, get_timestamp
from app.utils.validation import sanitize_filename, validate_patient_name

@dataclass
class Recording:
    """Recording model - all metadata optional."""
    
    # Required fields (auto-generated)
    filename: str
    recording_date: str
    recording_time: str
    created_timestamp: str
    modified_timestamp: str
    
    # Optional metadata
    id: Optional[int] = None
    filepath: Optional[str] = None
    patient_name: Optional[str] = None
    procedure_name: Optional[str] = None
    operating_theatre: Optional[str] = None
    surgeon_name: Optional[str] = None
    notes: Optional[str] = None
    
    # Video metadata
    duration_seconds: int = 0
    file_size_bytes: int = 0
    video_codec: Optional[str] = None
    resolution: Optional[str] = None
    framerate: int = 30
    thumbnail_path: Optional[str] = None
    
    @classmethod
    def create_new(cls) -> 'Recording':
        """Create new recording with auto-generated filename."""
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")
        filename = f"{date_str}_{time_str}_001.mp4"
        
        return cls(
            filename=filename,
            recording_date=get_date(),
            recording_time=get_time(),
            created_timestamp=get_timestamp(),
            modified_timestamp=get_timestamp()
        )
    
    def update_filename_from_patient(self):
        """Update filename to include patient name."""
        if self.patient_name:
            safe_name = sanitize_filename(self.patient_name)
            # Extract timestamp from existing filename
            parts = self.filename.split('_')
            if len(parts) >= 3:
                date = parts[0]
                time = parts[1]
                self.filename = f"{safe_name}_{date}_{time}_001.mp4"
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate recording data."""
        errors = []
        
        if self.patient_name:
            valid, error = validate_patient_name(self.patient_name)
            if not valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    def get_display_name(self) -> str:
        """Get display name for UI."""
        return self.patient_name if self.patient_name else self.filename
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database."""
        return {
            'id': self.id,
            'filename': self.filename,
            'filepath': self.filepath,
            'recording_date': self.recording_date,
            'recording_time': self.recording_time,
            'duration_seconds': self.duration_seconds,
            'file_size_bytes': self.file_size_bytes,
            'patient_name': self.patient_name,
            'procedure_name': self.procedure_name,
            'operating_theatre': self.operating_theatre,
            'surgeon_name': self.surgeon_name,
            'notes': self.notes,
            'video_codec': self.video_codec,
            'resolution': self.resolution,
            'framerate': self.framerate,
            'thumbnail_path': self.thumbnail_path,
            'created_timestamp': self.created_timestamp,
            'modified_timestamp': self.modified_timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Recording':
        """Create from dictionary."""
        return cls(**data)
