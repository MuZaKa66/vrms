"""
File: app/gui/widgets/recording_timer.py

Module Description:
    Recording timer widget.
    
    Large display of recording duration.

Author: OT Video Dev Team
Date: January 30, 2026
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from app.utils.logger import AppLogger

logger = AppLogger("RecordingTimerWidget")


class RecordingTimerWidget(QWidget):
    """
    Recording timer display widget.
    
    Large, clear timer for recording duration.
    
    Methods:
        start(): Start timer
        stop(): Stop timer
        reset(): Reset to 00:00:00
        get_elapsed(): Get elapsed seconds
    
    Example:
        >>> timer = RecordingTimerWidget()
        >>> timer.start()
        >>> # ... recording ...
        >>> timer.stop()
        >>> print(timer.get_elapsed())
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.elapsed_seconds = 0
        self.is_running = False
        
        self.init_ui()
        
        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Timer display
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #3498db;")
        
        layout.addWidget(self.time_label)
    
    def start(self):
        """Start timer."""
        self.is_running = True
        self.timer.start(1000)  # Update every second
        logger.debug("Timer started")
    
    def stop(self):
        """Stop timer."""
        self.is_running = False
        self.timer.stop()
        logger.debug(f"Timer stopped at {self.elapsed_seconds}s")
    
    def reset(self):
        """Reset timer."""
        self.elapsed_seconds = 0
        self.update_display()
        logger.debug("Timer reset")
    
    def update_display(self):
        """Update time display."""
        if self.is_running:
            self.elapsed_seconds += 1
        
        hours = self.elapsed_seconds // 3600
        minutes = (self.elapsed_seconds % 3600) // 60
        seconds = self.elapsed_seconds % 60
        
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def get_elapsed(self):
        """Get elapsed seconds."""
        return self.elapsed_seconds
    
    def set_color(self, color: str):
        """Set display color."""
        self.time_label.setStyleSheet(f"color: {color};")


__all__ = ['RecordingTimerWidget']