"""
File: app/gui/export_dialog.py

Module Description:
    Export to USB dialog.

Author: OT Video Dev Team
Date: January 30, 2026

"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QPushButton,
    QProgressBar, QMessageBox
)
from typing import List

from app.controllers.export_controller import ExportController
from app.models.recording import Recording

class ExportDialog(QDialog):
    """Export to USB dialog."""
    
    def __init__(self, recordings: List[Recording], parent=None):
        super().__init__(parent)
        self.recordings = recordings
        self.controller = ExportController()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("Export to USB")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel(f"Exporting {len(self.recordings)} recording(s)")
        layout.addWidget(info)
        
        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        # Status
        self.status_label = QLabel("Detecting USB...")
        layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Start Export")
        self.export_btn.clicked.connect(self.start_export)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Detect USB
        self.detect_usb()
    
    def detect_usb(self):
        """Detect USB devices."""
        success, devices, error = self.controller.detect_usb()
        
        if not success or not devices:
            self.status_label.setText("No USB detected. Please insert USB drive.")
            self.export_btn.setEnabled(False)
        else:
            self.usb_device = devices[0]
            self.status_label.setText(f"USB detected: {self.usb_device}")
            self.export_btn.setEnabled(True)
    
    def start_export(self):
        """Start export process."""
        # Create job
        rec_ids = [r.id for r in self.recordings if r.id]
        success, job, error = self.controller.create_export_job(
            rec_ids, self.usb_device
        )
        
        if not success:
            QMessageBox.warning(self, "Error", error)
            return
        
        # Export
        self.export_btn.setEnabled(False)
        self.status_label.setText("Exporting...")
        
        success, _, error = self.controller.start_export(job)
        
        if success:
            self.progress.setValue(100)
            QMessageBox.information(self, "Success", "Export completed!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", error)
            self.reject()


__all__ = ['ExportDialog']