"""
File: app/gui/widgets/video_thumbnail.py

Module Description:
    Video thumbnail display widget.
    
    Shows thumbnail image with recording info.

Author: OT Video Dev Team
Date: January 30, 2026
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from app.models.recording import Recording
from app.utils.logger import AppLogger

logger = AppLogger("VideoThumbnailWidget")


class VideoThumbnailWidget(QWidget):
    """
    Video thumbnail widget.
    
    Displays thumbnail image and recording info.
    
    Methods:
        set_recording(recording): Display recording info
        set_thumbnail(image_path): Load thumbnail image
    
    Example:
        >>> thumb = VideoThumbnailWidget()
        >>> thumb.set_recording(recording)
        >>> thumb.set_thumbnail("/path/to/thumb.jpg")
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Thumbnail image
        self.image_label = QLabel()
        self.image_label.setFixedSize(160, 120)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                border: 2px solid #2c3e50;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.image_label)
        
        # Info label
        self.info_label = QLabel("No recording")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
    
    def set_recording(self, recording: Recording):
        """Set recording to display."""
        self.recording = recording
        
        # Update info text
        display_name = recording.get_display_name()
        duration = recording.duration_seconds
        self.info_label.setText(
            f"{display_name}\n"
            f"{duration}s - {recording.recording_date}"
        )
        
        # Load thumbnail if available
        if recording.thumbnail_path:
            self.set_thumbnail(recording.thumbnail_path)
    
    def set_thumbnail(self, image_path: str):
        """Load and display thumbnail image."""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap)


__all__ = ['VideoThumbnailWidget']