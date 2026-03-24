"""
File: app/gui/widgets/voice_indicator_widget.py

Voice indicator widget - visual feedback for voice commands.
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QPainter

from app.utils.logger import AppLogger

logger = AppLogger("VoiceIndicator")


class VoiceIndicatorWidget(QWidget):
    """Voice command visual indicator."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.state = "idle"
        self.opacity_value = 1.0
        
        self.init_ui()
        self.setup_animation()
        
        logger.debug("Voice indicator initialized")
    
    def init_ui(self):
        """Build UI."""
        self.setFixedSize(120, 120)
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon
        self.icon_label = QLabel("🎤")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFont(QFont("Arial", 48))
        self.icon_label.setStyleSheet(
            "background-color: rgba(52, 73, 94, 200); border-radius: 60px;"
        )
        layout.addWidget(self.icon_label)
        
        # Status
        self.status_label = QLabel("Voice Control")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.status_label.setStyleSheet(
            "color: #34495e; background-color: transparent;"
        )
        layout.addWidget(self.status_label)
    
    def setup_animation(self):
        """Setup pulse animation."""
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.3)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setLoopCount(-1)
    
    def set_idle(self):
        """Set to idle state."""
        self.state = "idle"
        self.animation.stop()
        self.opacity_value = 1.0
        
        self.icon_label.setText("🎤")
        self.icon_label.setStyleSheet(
            "background-color: rgba(149, 165, 166, 200); border-radius: 60px;"
        )
        self.status_label.setText("Voice Control")
        self.status_label.setStyleSheet("color: #95a5a6; background-color: transparent;")
        
        self.update()
        logger.debug("State: IDLE")
    
    def set_listening(self):
        """Set to listening state."""
        self.state = "listening"
        
        self.icon_label.setText("🎤")
        self.icon_label.setStyleSheet(
            "background-color: rgba(52, 152, 219, 200); border-radius: 60px;"
        )
        self.status_label.setText("Listening...")
        self.status_label.setStyleSheet("color: #3498db; background-color: transparent;")
        
        self.animation.start()
        
        logger.debug("State: LISTENING")
    
    def set_recognized(self):
        """Flash success."""
        self.state = "recognized"
        self.animation.stop()
        self.opacity_value = 1.0
        
        self.icon_label.setText("✓")
        self.icon_label.setStyleSheet(
            "background-color: rgba(39, 174, 96, 200); border-radius: 60px;"
        )
        self.status_label.setText("Recognized!")
        self.status_label.setStyleSheet("color: #27ae60; background-color: transparent;")
        
        self.update()
        
        QTimer.singleShot(1000, self.set_idle)
        
        logger.debug("State: RECOGNIZED")
    
    def set_error(self, message="Not recognized"):
        """Show error."""
        self.animation.stop()
        self.opacity_value = 1.0
        
        self.icon_label.setText("✗")
        self.icon_label.setStyleSheet(
            "background-color: rgba(231, 76, 60, 200); border-radius: 60px;"
        )
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
        
        self.update()
        
        QTimer.singleShot(2000, self.set_idle)
        
        logger.debug(f"State: ERROR ({message})")
    
    def get_opacity(self):
        return self.opacity_value
    
    def set_opacity(self, value):
        self.opacity_value = value
        self.update()
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def paintEvent(self, event):
        """Apply opacity."""
        painter = QPainter(self)
        painter.setOpacity(self.opacity_value)
        painter.fillRect(self.rect(), Qt.transparent)
        super().paintEvent(event)
    
    def mousePressEvent(self, event):
        """Handle click."""
        logger.debug("Indicator clicked")
        super().mousePressEvent(event)


__all__ = ['VoiceIndicatorWidget']