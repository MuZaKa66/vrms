"""
Recording model - zero-friction design.
Timestamp to second is unique - no need for _001 suffix.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple, List
from app.utils.datetime_utils import get_date, get_time, get_timestamp
from app.utils.validation import sanitize_filename, validate_patient_name

@dataclass
class Recording:
    """
    Recording data model - metadata optional.
    
    DESIGN: Timestamp-based filenames (unique to second).
    Format: 20260213_143052.mp4 (no _001 needed)
    """
    
    # Auto-generated (required)
    filename: str
    recording_date: str
    recording_time: str
    created_timestamp: str
    modified_timestamp: str
    
    # User metadata (optional)
    id: Optional[int] = None
    filepath: Optional[str] = None
    patient_name: Optional[str] = None
    procedure_name: Optional[str] = None
    operating_theatre: Optional[str] = None
    surgeon_name: Optional[str] = None
    notes: Optional[str] = None
    
    # Video metadata (auto-populated)
    duration_seconds: int = 0
    file_size_bytes: int = 0
    video_codec: Optional[str] = None
    resolution: Optional[str] = None
    framerate: int = 30
    thumbnail_path: Optional[str] = None
    
    @classmethod
    def create_new(cls) -> 'Recording':
        """
        Create new recording with timestamp-based filename.
        
        CHANGED: No _001 suffix - timestamp to second is unique enough.
        Format: YYYYMMDD_HHMMSS.mp4
        Example: 20260213_143052.mp4
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")
        filename = f"{date_str}_{time_str}.mp4"  # ← NO _001
        
        return cls(
            filename=filename,
            recording_date=get_date(),
            recording_time=get_time(),
            created_timestamp=get_timestamp(),
            modified_timestamp=get_timestamp()
        )
    
    def update_filename_from_patient(self):
        """
        Update filename to include patient name.
        Preserves timestamp for uniqueness.
        """
        if self.patient_name:
            safe_name = sanitize_filename(self.patient_name)
            parts = self.filename.split('_')
            if len(parts) >= 2:
                date = parts[0]
                time = parts[1].replace('.mp4', '')
                self.filename = f"{safe_name}_{date}_{time}.mp4"  # ← NO _001
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate recording data."""
        errors = []
        if self.patient_name:
            valid, error = validate_patient_name(self.patient_name)
            if not valid:
                errors.append(error)
        return len(errors) == 0, errors
    
    def get_display_name(self) -> str:
        """Get UI display name."""
        return self.patient_name if self.patient_name else self.filename
    
    def to_dict(self) -> dict:
        """Convert to dict for database."""
        return {
            'id': self.id, 'filename': self.filename, 'filepath': self.filepath,
            'recording_date': self.recording_date, 'recording_time': self.recording_time,
            'duration_seconds': self.duration_seconds, 'file_size_bytes': self.file_size_bytes,
            'patient_name': self.patient_name, 'procedure_name': self.procedure_name,
            'operating_theatre': self.operating_theatre, 'surgeon_name': self.surgeon_name,
            'notes': self.notes, 'video_codec': self.video_codec,
            'resolution': self.resolution, 'framerate': self.framerate,
            'thumbnail_path': self.thumbnail_path,
            'created_timestamp': self.created_timestamp,
            'modified_timestamp': self.modified_timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Recording':
        """Create from dict."""
        return cls(**data)
