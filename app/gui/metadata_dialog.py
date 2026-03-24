"""
File: app/gui/metadata_dialog.py

═══════════════════════════════════════════════════════════════════════════
RECORDING INFORMATION DIALOG - User-Friendly & Robust
═══════════════════════════════════════════════════════════════════════════

CHANGES FROM PREVIOUS VERSION:
1. "Metadata" → "Recording Info" (doctor-friendly terminology)
2. Added comprehensive error handling with user notifications
3. Database save errors now show friendly messages
4. All existing functionality preserved

PURPOSE:
    Dialog for entering patient/procedure information.
    
    Used in TWO scenarios:
    1. BEFORE recording (Add Info button) - just collects data
    2. AFTER recording (Stop button) - collects and saves data

SECTION INDEX:
    SECTION 1: Imports & Initialization
    SECTION 2: UI Layout Construction
    SECTION 3: Save Recording Info (post-recording with error handling)
    SECTION 4: Get Recording Info (pre-recording)
    
Author: OT Video Dev Team
Date: February 13, 2026
Version: 2.0.0 (User-friendly + robust error handling)
"""

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: IMPORTS & INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.models.metadata import RecordingMetadata, CommonProcedures
from app.controllers.metadata_controller import MetadataController
from app.utils.logger import AppLogger

logger = AppLogger("RecordingInfoDialog")


class MetadataDialog(QDialog):
    """
    Recording information entry dialog.
    
    USAGE SCENARIOS:
    
    1. Pre-recording (recording = None):
        - User clicks "Add Info" before recording
        - Dialog just collects data
        - Data stored temporarily in recording_screen
        - When recording stops, data auto-saved
        
    2. Post-recording (recording object passed):
        - User stops recording
        - Dialog collects and SAVES data immediately
        - Updates database with recording info
        
    ERROR HANDLING:
    - Database save errors show user-friendly messages
    - Recording is safe even if info save fails
    - All errors logged for debugging
    """
    
    def __init__(self, recording=None, parent=None):
        """
        Initialize dialog.
        
        Args:
            recording: Recording object (None for pre-recording)
            parent: Parent widget
        """
        super().__init__(parent)
        self.recording = recording
        self.init_ui()
        
        logger.debug("Recording info dialog initialized")
    
    # ════════════════════════════════════════════════════════════════════
    # SECTION 2: UI LAYOUT CONSTRUCTION
    # ════════════════════════════════════════════════════════════════════
    
    def init_ui(self):
        """Build dialog UI with user-friendly labels."""
        # CHANGED: "Add Metadata" → "Add Recording Info"
        self.setWindowTitle("Add Recording Info")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title - CHANGED: "Recording Metadata" → "Recording Information"
        title = QLabel("Recording Information")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # Patient Name
        layout.addWidget(QLabel("Patient Name:"))
        self.patient_input = QLineEdit()
        self.patient_input.setPlaceholderText("Enter patient name")
        self.patient_input.setMinimumHeight(40)
        self.patient_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        layout.addWidget(self.patient_input)
        
        # Procedure Type
        layout.addWidget(QLabel("Procedure Type:"))
        self.procedure_combo = QComboBox()
        self.procedure_combo.addItems(CommonProcedures.get_all_names())
        self.procedure_combo.setMinimumHeight(40)
        self.procedure_combo.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.procedure_combo)
        
        # Operating Theatre
        layout.addWidget(QLabel("Operating Theatre:"))
        self.ot_combo = QComboBox()
        self.ot_combo.addItems(["OT 1", "OT 2", "OT 3", "OT 4", "OT 5"])
        self.ot_combo.setMinimumHeight(40)
        self.ot_combo.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.ot_combo)
        
        # Consultant/Surgeon
        layout.addWidget(QLabel("Consultant/Surgeon:"))
        self.consultant_input = QLineEdit()
        self.consultant_input.setPlaceholderText("Enter surgeon name")
        self.consultant_input.setMinimumHeight(40)
        self.consultant_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        layout.addWidget(self.consultant_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumSize(120, 50)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setMinimumSize(120, 50)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    # ════════════════════════════════════════════════════════════════════
    # SECTION 3: SAVE RECORDING INFO (with robust error handling)
    # ════════════════════════════════════════════════════════════════════
    
    def accept(self):
        """
        Save dialog data.
        
        ROBUST ERROR HANDLING:
        - Shows user-friendly error messages
        - Recording is safe even if info save fails
        - All errors logged for debugging
        """
        # If recording object provided, save to database
        if self.recording:
            try:
                # Get metadata
                metadata = self.get_metadata()
                
                # Save to database
                meta_controller = MetadataController()
                success, updated_recording, error = meta_controller.add_metadata(
                    self.recording,
                    metadata
                )
                
                # ROBUST: Check for save errors
                if not success:
                    # Show user-friendly error message
                    QMessageBox.warning(
                        self,
                        "Save Error",
                        f"Recording is saved successfully!\n\n"
                        f"However, the recording information could not be saved:\n"
                        f"{error}\n\n"
                        f"You can add this information later by editing the recording."
                    )
                    logger.error(f"Recording info save failed: {error}")
                    # Still accept dialog - recording is safe
                    super().accept()
                    return
                
                logger.info(f"Recording info saved for: {self.recording.filename}")
                super().accept()
            
            except Exception as e:
                # ROBUST: Catch unexpected errors
                QMessageBox.critical(
                    self,
                    "Unexpected Error",
                    f"An unexpected error occurred while saving:\n\n{str(e)}\n\n"
                    f"Your recording is safe, but information was not saved.\n"
                    f"Please contact support if this continues."
                )
                logger.error(f"Exception in recording info save: {e}", exc_info=True)
                # Still accept dialog - recording is safe
                super().accept()
        else:
            # Pre-recording mode - just accept without saving
            super().accept()
    
    # ════════════════════════════════════════════════════════════════════
    # SECTION 4: GET RECORDING INFO (pre-recording)
    # ════════════════════════════════════════════════════════════════════
    
    def get_metadata(self) -> RecordingMetadata:
        """
        Get metadata from dialog inputs.
        
        CRITICAL METHOD for pre-recording workflow:
        - Called by recording_screen when "Add Info" clicked
        - Returns RecordingMetadata object with user inputs
        - Data stored temporarily until recording stops
        
        Returns:
            RecordingMetadata: Object with all form data
        """
        metadata = RecordingMetadata()
        
        # Get form values
        metadata.patient_name = self.patient_input.text().strip()
        metadata.procedure = self.procedure_combo.currentText()
        metadata.operating_theatre = self.ot_combo.currentText()
        metadata.surgeon_name = self.consultant_input.text().strip()
        
        logger.debug(f"Collected recording info: patient={metadata.patient_name}")
        
        return metadata


__all__ = ['MetadataDialog']


# ═══════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════
"""
SCENARIO 1: Pre-recording (Add Info button)
-------------------------------------------
# In recording_screen.py:
dialog = MetadataDialog(None, self)  # recording=None
if dialog.exec_():
    self.metadata = dialog.get_metadata()  # Store temporarily
    # Data auto-saved when recording stops

SCENARIO 2: Post-recording (Stop button)
-----------------------------------------
# In recording_screen.py:
dialog = MetadataDialog(recording, self)  # Pass recording object
if dialog.exec_():
    # Data saved to database immediately
    # Error handling built-in
"""
