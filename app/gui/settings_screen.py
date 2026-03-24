"""
File: app/gui/settings_screen.py

Module Description:
    Settings and system information screen.
    
    Features:
    - System information display
    - Application shutdown button
    - Storage statistics
    - About information
    
    Simple, clean interface for system management.

Author: OT Video Dev Team
Date: February 5, 2026
Version: 2.0.0 (Enhanced)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont

from app.services.storage_service import StorageService
from app.utils.logger import AppLogger
from config.app_config import APP_NAME, APP_VERSION

logger = AppLogger("SettingsScreen")


class SettingsScreen(QWidget):
    """
    Settings and system information screen.
    
    Displays system stats and provides shutdown option.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = StorageService()
        self.init_ui()
        self.update_stats()
        
        logger.info("Settings screen initialized")
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Settings & Information")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # App Info Section
        app_group = QGroupBox("Application Information")
        app_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        app_layout = QVBoxLayout()
        
        app_name_label = QLabel(f"<b>{APP_NAME}</b>")
        app_name_label.setFont(QFont("Arial", 18))
        
        version_label = QLabel(f"Version: {APP_VERSION}")
        version_label.setStyleSheet("color: gray; font-size: 14px;")
        
        description_label = QLabel(
            "Professional video recording system for operating theatres.\n"
            "Secure, air-gapped, HIPAA/GDPR compliant."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 13px; color: #34495e;")
        
        app_layout.addWidget(app_name_label)
        app_layout.addWidget(version_label)
        app_layout.addWidget(description_label)
        
        app_group.setLayout(app_layout)
        layout.addWidget(app_group)
        
        # Storage Info Section
        storage_group = QGroupBox("Storage Information")
        storage_group.setStyleSheet(app_group.styleSheet())
        
        storage_layout = QVBoxLayout()
        
        self.storage_info_label = QLabel("Loading...")
        self.storage_info_label.setFont(QFont("Arial", 14))
        self.storage_info_label.setWordWrap(True)
        
        refresh_storage_btn = QPushButton("Refresh Stats")
        refresh_storage_btn.setMaximumWidth(150)
        refresh_storage_btn.setMinimumHeight(40)
        refresh_storage_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        refresh_storage_btn.clicked.connect(self.update_stats)
        
        storage_layout.addWidget(self.storage_info_label)
        storage_layout.addWidget(refresh_storage_btn)
        
        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)
        
        # System Info Section
        system_group = QGroupBox("System Information")
        system_group.setStyleSheet(app_group.styleSheet())
        
        system_layout = QVBoxLayout()
        
        import platform
        system_info = f"""
        <b>Platform:</b> {platform.system()} {platform.release()}<br>
        <b>Machine:</b> {platform.machine()}<br>
        <b>Python:</b> {platform.python_version()}
        """
        
        system_label = QLabel(system_info)
        system_label.setFont(QFont("Arial", 13))
        
        system_layout.addWidget(system_label)
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        layout.addStretch()
        
        # Shutdown Button (prominent, bottom)
        shutdown_frame = QFrame()
        shutdown_frame.setFrameStyle(QFrame.StyledPanel)
        shutdown_frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        shutdown_layout = QVBoxLayout(shutdown_frame)
        
        warning_label = QLabel("⚠️  Closing the application will stop any active recording")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
        
        shutdown_btn = QPushButton("Shutdown Application")
        shutdown_btn.setMinimumSize(300, 80)
        shutdown_btn.setFont(QFont("Arial", 18, QFont.Bold))
        shutdown_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        shutdown_btn.clicked.connect(self.shutdown_application)
        
        shutdown_layout.addWidget(warning_label)
        shutdown_layout.addWidget(shutdown_btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(shutdown_frame)
    
    def update_stats(self):
        """Update storage statistics."""
        success, stats, error = self.storage.get_storage_status()
        
        if success:
            total_gb = stats.get('total_gb', 0)
            used_gb = stats.get('used_gb', 0)
            free_gb = stats.get('free_gb', 0)
            percent = stats.get('percent_used', 0)
            
            # Determine status color
            if free_gb < 10:
                status_color = "#e74c3c"  # Red - critical
                status_text = "⚠️ CRITICAL"
            elif free_gb < 20:
                status_color = "#f39c12"  # Orange - warning
                status_text = "⚠️ LOW"
            else:
                status_color = "#27ae60"  # Green - OK
                status_text = "✓ OK"
            
            info_text = f"""
            <p><b>Status:</b> <span style='color: {status_color};'>{status_text}</span></p>
            <p><b>Total Space:</b> {total_gb:.1f} GB</p>
            <p><b>Used:</b> {used_gb:.1f} GB ({percent:.1f}%)</p>
            <p><b>Free:</b> {free_gb:.1f} GB</p>
            """
            
            if free_gb < 20:
                info_text += f"<p style='color: {status_color};'><b>Action needed:</b> Export old recordings or free up space</p>"
            
            self.storage_info_label.setText(info_text)
            logger.debug(f"Storage stats updated: {free_gb:.1f} GB free")
        else:
            self.storage_info_label.setText(f"<span style='color: #e74c3c;'>Error: {error}</span>")
    
    def shutdown_application(self):
        """Shutdown application with confirmation."""
        # Check if recording is active
        from app.utils.constants import RecordingState
        from app.controllers.recording_controller import RecordingController
        
        controller = RecordingController()
        
        if controller.state == RecordingState.RECORDING:
            QMessageBox.warning(
                self,
                "Recording in Progress",
                "Recording is currently active!\n\n"
                "Please stop recording before shutting down the application.",
                QMessageBox.Ok
            )
            return
        
        # Confirm shutdown
        reply = QMessageBox.question(
            self,
            "Confirm Shutdown",
            "Are you sure you want to close the application?\n\n"
            "All unsaved work will be lost.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("Application shutdown requested by user")
            QMessageBox.information(
                self,
                "Shutting Down",
                "Application is closing.\nThank you for using OT Video System!"
            )
            
            # Close application
            QCoreApplication.quit()


__all__ = ['SettingsScreen']
