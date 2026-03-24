"""
File: app/gui/widgets/video_player.py

Module Description:
    Video player widget for playback.
    
    Features:
    - Play/pause controls
    - Seek bar
    - Volume control
    - Fullscreen toggle

Author: OT Video Dev Team
Date: January 30, 2026
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from app.utils.logger import AppLogger

logger = AppLogger("VideoPlayerWidget")


class VideoPlayerWidget(QWidget):
    """
    Video player widget.
    
    Simple video playback with controls.
    
    Methods:
        load_video(filepath): Load video file
        play(): Start playback
        pause(): Pause playback
        stop(): Stop playback
        set_position(seconds): Seek to position
    
    Example:
        >>> player = VideoPlayerWidget()
        >>> player.load_video("/path/to/video.mp4")
        >>> player.play()
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Media player
        self.player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)
        
        self.init_ui()
        
        # Connect signals
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        
        logger.info("Video player widget initialized")
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video display
        layout.addWidget(self.video_widget)
        
        # Controls
        controls = QWidget()
        controls.setStyleSheet("background-color: #2c3e50;")
        controls_layout = QHBoxLayout(controls)
        
        # Play/Pause button
        self.play_btn = QPushButton("▶")
        self.play_btn.setMinimumSize(60, 60)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 24px;
                border-radius: 30px;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        
        # Time labels
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white;")
        
        # Add to layout
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.time_label)
        
        layout.addWidget(controls)
    
    def load_video(self, filepath: str):
        """Load video file."""
        media = QMediaContent(QUrl.fromLocalFile(filepath))
        self.player.setMedia(media)
        logger.info(f"Loaded video: {filepath}")
    
    def play(self):
        """Start playback."""
        self.player.play()
        self.play_btn.setText("⏸")
    
    def pause(self):
        """Pause playback."""
        self.player.pause()
        self.play_btn.setText("▶")
    
    def stop(self):
        """Stop playback."""
        self.player.stop()
        self.play_btn.setText("▶")
    
    def toggle_play(self):
        """Toggle play/pause."""
        if self.player.state() == QMediaPlayer.PlayingState:
            self.pause()
        else:
            self.play()
    
    def set_position(self, position):
        """Seek to position."""
        self.player.setPosition(position)
    
    def position_changed(self, position):
        """Update position slider."""
        self.position_slider.setValue(position)
        
        # Update time label
        current = self.format_time(position)
        total = self.format_time(self.player.duration())
        self.time_label.setText(f"{current} / {total}")
    
    def duration_changed(self, duration):
        """Update slider range."""
        self.position_slider.setRange(0, duration)
    
    def format_time(self, ms):
        """Format milliseconds to MM:SS."""
        seconds = ms // 1000
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"


__all__ = ['VideoPlayerWidget']