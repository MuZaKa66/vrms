
"""
File: app/gui/widgets/video_list_item.py

Module Description:
    Custom list item for video library.

Author: OT Video Dev Team
Date: January 30, 2026
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from app.models.recording import Recording

class VideoListItemWidget(QWidget):
    """Custom video list item."""
    
    def __init__(self, recording: Recording, parent=None):
        super().__init__(parent)
        self.recording = recording
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QHBoxLayout(self)
        
        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(80, 60)
        thumb_label.setStyleSheet("background-color: #34495e; border-radius: 3px;")
        
        if self.recording.thumbnail_path:
            pixmap = QPixmap(self.recording.thumbnail_path)
            thumb_label.setPixmap(pixmap.scaled(80, 60, Qt.KeepAspectRatio))
        
        layout.addWidget(thumb_label)
        
        # Info
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.recording.get_display_name())
        name_label.setStyleSheet("font-weight: bold;")
        
        details_label = QLabel(
            f"{self.recording.recording_date} - {self.recording.duration_seconds}s"
        )
        details_label.setStyleSheet("color: gray; font-size: 10px;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(details_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()


__all__ = ['VideoListItemWidget']