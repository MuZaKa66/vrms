"""
File: app/gui/widgets/storage_indicator.py

Module Description:
    Storage space indicator widget.
    
    Shows storage usage with progress bar and warnings.

Author: OT Video Dev Team
Date: January 30, 2026
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer

from app.services.storage_service import StorageService
from app.utils.logger import AppLogger

logger = AppLogger("StorageIndicatorWidget")


class StorageIndicatorWidget(QWidget):
    """
    Storage indicator widget.
    
    Displays storage space with color-coded warnings.
    
    Methods:
        update_status(): Refresh storage info
        start_monitoring(interval): Auto-update every N seconds
    
    Example:
        >>> indicator = StorageIndicatorWidget()
        >>> indicator.start_monitoring(5)  # Update every 5 seconds
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = StorageService()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Storage")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Info label
        self.info_label = QLabel("Checking...")
        layout.addWidget(self.info_label)
        
        # Initial update
        self.update_status()
    
    def update_status(self):
        """Update storage status."""
        success, status, error = self.storage.get_storage_status()
        
        if not success:
            self.info_label.setText("Storage check failed")
            return
        
        # Update progress bar
        percent_used = status['percent_used']
        self.progress_bar.setValue(int(percent_used))
        
        # Update info
        free_gb = status['free_gb']
        total_gb = status['total_gb']
        self.info_label.setText(
            f"{free_gb:.1f} GB free of {total_gb:.1f} GB"
        )
        
        # Color code based on status
        if status['is_critical']:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #e74c3c;
                }
            """)
            self.info_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        elif status['is_low']:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #f39c12;
                }
            """)
            self.info_label.setStyleSheet("color: #f39c12;")
        else:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #27ae60;
                }
            """)
            self.info_label.setStyleSheet("color: #27ae60;")
    
    def start_monitoring(self, interval_seconds: int = 5):
        """Start auto-updating."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(interval_seconds * 1000)


__all__ = ['StorageIndicatorWidget']