"""
File: app/models/metadata.py

Metadata model for recordings.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple

@dataclass
class RecordingMetadata:
    """Recording metadata - all optional."""
    
    patient_name: Optional[str] = None
    procedure: Optional[str] = None
    diagnosis: Optional[str] = None
    operating_theatre: Optional[str] = None
    surgeon_name: Optional[str] = None
    assistant_name: Optional[str] = None
    notes: Optional[str] = None
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate metadata."""
        errors = []
        
        if self.patient_name and len(self.patient_name) > 100:
            errors.append("Patient name too long (max 100 characters)")
        
        if self.notes and len(self.notes) > 1000:
            errors.append("Notes too long (max 1000 characters)")
        
        return len(errors) == 0, errors
    
    def sanitize(self):
        """Sanitize metadata fields."""
        if self.patient_name:
            self.patient_name = self.patient_name.strip()
        if self.procedure:
            self.procedure = self.procedure.strip()
        if self.notes:
            self.notes = self.notes.strip()
    
    def apply_to_recording(self, recording):
        """Apply metadata to recording object."""
        if self.patient_name:
            recording.patient_name = self.patient_name
            recording.update_filename_from_patient()
        if self.procedure:
            recording.procedure_name = self.procedure
        if self.operating_theatre:
            recording.operating_theatre = self.operating_theatre
        if self.surgeon_name:
            recording.surgeon_name = self.surgeon_name
        if self.notes:
            recording.notes = self.notes


class CommonProcedures:
    """Common procedure names."""
    
    PROCEDURES = [
        "Cataract Surgery",
        "Glaucoma Surgery",
        "Retinal Surgery",
        "Corneal Transplant",
        "Oculoplastic Surgery",
        "Other"
    ]
    
    @classmethod
    def get_all_names(cls) -> List[str]:
        """Get all procedure names."""
        return cls.PROCEDURES


class MetadataPresets:
    """Metadata presets for quick entry."""
    
    @staticmethod
    def emergency_surgery() -> RecordingMetadata:
        """Emergency surgery preset."""
        return RecordingMetadata(
            operating_theatre="Emergency OT",
            notes="Emergency procedure"
        )
    
    @staticmethod
    def teaching_case() -> RecordingMetadata:
        """Teaching case preset."""
        return RecordingMetadata(
            notes="Teaching case - for educational purposes"
        )
    
    @staticmethod
    def routine_cataract() -> RecordingMetadata:
        """Routine cataract surgery preset."""
        return RecordingMetadata(
            procedure="Cataract Surgery",
            operating_theatre="OT_1"
        )
