"""
File: app/models/export_job.py

Export job model for USB export tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum, auto

class ExportStatus(Enum):
    """Export status enumeration."""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()

@dataclass
class ExportJob:
    """Export job for tracking USB exports."""
    
    recording_ids: List[int]
    destination: str
    status: ExportStatus = ExportStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    files_exported: int = 0
    total_files: int = 0
    
    @classmethod
    def create_new(cls, recording_ids: List[int], destination: str) -> 'ExportJob':
        """Create new export job."""
        return cls(
            recording_ids=recording_ids,
            destination=destination,
            total_files=len(recording_ids)
        )
    
    def start(self):
        """Mark as started."""
        self.status = ExportStatus.IN_PROGRESS
        self.started_at = datetime.now().isoformat()
    
    def mark_completed(self):
        """Mark as completed."""
        self.status = ExportStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
    
    def mark_failed(self, error: str):
        """Mark as failed."""
        self.status = ExportStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now().isoformat()
    
    def get_progress_percent(self) -> int:
        """Get progress percentage."""
        if self.total_files == 0:
            return 0
        return int((self.files_exported / self.total_files) * 100)
    
    def get_detailed_status(self) -> dict:
        """Get detailed status information."""
        return {
            'status': self.status.name,
            'progress_percent': self.get_progress_percent(),
            'files_exported': self.files_exported,
            'total_files': self.total_files,
            'destination': self.destination,
            'error': self.error_message,
            'message': self._get_status_message()
        }
    
    def _get_status_message(self) -> str:
        """Get user-friendly status message."""
        if self.status == ExportStatus.PENDING:
            return "Waiting to start export..."
        elif self.status == ExportStatus.IN_PROGRESS:
            return f"Exporting {self.files_exported}/{self.total_files} files..."
        elif self.status == ExportStatus.COMPLETED:
            return f"Successfully exported {self.files_exported} files"
        elif self.status == ExportStatus.FAILED:
            return f"Export failed: {self.error_message}"
        elif self.status == ExportStatus.CANCELLED:
            return "Export cancelled"
        return "Unknown status"
