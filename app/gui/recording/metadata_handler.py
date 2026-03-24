"""
Metadata Handler - Patient and Procedure Info Management

Handles all metadata-related operations:
- Showing metadata dialog
- Storing metadata
- Displaying metadata info
- Clearing metadata

Author: OT Video Dev Team
Date: February 16, 2026
Version: 2.0.0 (Refactored)
"""

from PyQt5.QtWidgets import QMessageBox

from app.gui.metadata_dialog import MetadataDialog
from app.models.metadata import RecordingMetadata
from app.controllers.metadata_controller import MetadataController
from app.utils.logger import AppLogger

logger = AppLogger("MetadataHandler")


class MetadataHandler:
    """
    Manages patient and procedure metadata for recordings.
    
    Responsibilities:
    - Show metadata dialog for data entry
    - Store metadata temporarily
    - Format metadata for display
    - Clear metadata when requested
    - Save metadata to database after recording
    
    Attributes:
        metadata (RecordingMetadata): Current metadata object
        info_display_label (QLabel): Label widget for displaying info
        info_btn (QPushButton): Add/Edit Info button
        clear_btn (QPushButton): Clear button
    """
    
    def __init__(self, info_display_label, info_btn, clear_btn, parent_widget):
        """
        Initialize metadata handler.
        
        Args:
            info_display_label: QLabel for displaying "Patient: John Doe"
            info_btn: QPushButton for Add/Edit Info
            clear_btn: QPushButton for Clear
            parent_widget: Parent widget for dialog (usually recording_screen)
        """
        self.metadata = RecordingMetadata()
        self.info_display_label = info_display_label
        self.info_btn = info_btn
        self.clear_btn = clear_btn
        self.parent_widget = parent_widget
        
        logger.debug("MetadataHandler initialized")
    
    def has_metadata(self):
        """
        Check if any metadata exists.
        
        Returns:
            bool: True if patient name or procedure exists
        """
        return bool(self.metadata.patient_name or self.metadata.procedure)
    
    def show_metadata_dialog(self, recording=None):
        """
        Show metadata dialog for data entry.
        
        Args:
            recording: Recording object (None for pre-recording, object for post-recording)
        
        Returns:
            bool: True if user saved, False if cancelled
        
        Workflow:
        - Pre-recording: recording=None, shows empty or pre-filled dialog
        - Post-recording: recording=object, dialog saves directly to database
        """
        dialog = MetadataDialog(recording, self.parent_widget)
        
        # Pre-fill if metadata exists
        if self.has_metadata() and recording is None:
            dialog.patient_input.setText(self.metadata.patient_name or "")
            dialog.procedure_combo.setCurrentText(self.metadata.procedure or "")
            dialog.ot_combo.setCurrentText(self.metadata.operating_theatre or "")
            dialog.surgeon_combo.setCurrentText(self.metadata.surgeon_name or "")
            dialog.notes_input.setPlainText(self.metadata.notes or "")
        
        # Show dialog
        result = dialog.exec_()
        
        if result:  # User clicked Save
            if recording is None:
                # Pre-recording: Store metadata temporarily
                self.metadata = dialog.get_metadata()
                self.update_display()
                logger.info("Metadata collected (pre-recording)")
                return True
            else:
                # Post-recording: Metadata already saved by dialog
                logger.info("Metadata saved (post-recording)")
                return True
        else:
            # User cancelled
            if recording is None:
                logger.info("Metadata dialog cancelled")
            return False
    
    def update_display(self):
        """
        Update the info display label with current metadata.
        
        Shows: "Patient: John Doe" (patient name only)
        or "" if no patient name
        
        Also updates button states:
        - Info button: "Edit Info" if has metadata, "Add Info" if not
        - Clear button: Shown if has metadata, hidden if not
        """
        if self.metadata.patient_name:
            # Show patient name
            self.info_display_label.setText(f"Patient: {self.metadata.patient_name}")
            
            # Update button states
            self.info_btn.setText("Edit Info")
            self.clear_btn.setVisible(True)
            
            # Update button style (warning color for Edit)
            from .design_constants import get_info_button_style
            self.info_btn.setStyleSheet(get_info_button_style(has_info=True))
        else:
            # No metadata - clear display
            self.info_display_label.setText("")
            
            # Update button states
            self.info_btn.setText("Add Info")
            self.clear_btn.setVisible(False)
            
            # Update button style (info color for Add)
            from .design_constants import get_info_button_style
            self.info_btn.setStyleSheet(get_info_button_style(has_info=False))
    
    def clear_metadata(self):
        """
        Clear all metadata and reset display.
        
        Resets:
        - Metadata object to empty
        - Info display label to blank
        - Button states to default
        """
        self.metadata = RecordingMetadata()
        self.update_display()
        logger.info("Metadata cleared")
    
    def confirm_clear(self):
        """
        Show confirmation dialog before clearing metadata.
        
        Returns:
            bool: True if user confirmed, False if cancelled
        """
        reply = QMessageBox.question(
            self.parent_widget,
            "Clear Recording Info",
            "Are you sure you want to clear all recording information?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_metadata()
            return True
        return False
    
    def save_to_database(self, recording):
        """
        Save metadata to database for a recording.
        
        Args:
            recording: Recording object to attach metadata to
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        
        Used for silent save workflow (voice mode or pre-filled info).
        """
        if not self.has_metadata():
            return True, None  # No metadata to save (not an error)
        
        try:
            meta_ctrl = MetadataController()
            success, _, error = meta_ctrl.add_metadata(recording, self.metadata)
            
            if success:
                logger.info(f"Metadata saved for recording: {recording.file_path}")
                return True, None
            else:
                logger.error(f"Failed to save metadata: {error}")
                return False, error
        
        except Exception as e:
            error_msg = f"Exception saving metadata: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_metadata_copy(self):
        """
        Get a copy of current metadata.
        
        Returns:
            RecordingMetadata: Copy of current metadata object
        
        Useful for passing to recording controller without modifying original.
        """
        return RecordingMetadata(
            patient_name=self.metadata.patient_name,
            procedure=self.metadata.procedure,
            operating_theatre=self.metadata.operating_theatre,
            surgeon_name=self.metadata.surgeon_name,
            notes=self.metadata.notes
        )


__all__ = ['MetadataHandler']
