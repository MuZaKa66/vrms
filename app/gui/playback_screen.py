"""
File: app/gui/playback_screen.py

═══════════════════════════════════════════════════════════════════════════
PLAYBACK SCREEN - Robust File Finding & Intuitive Layout
═══════════════════════════════════════════════════════════════════════════

IMPROVEMENTS:
1. Back button moved to TOP-LEFT (more intuitive)
2. Smart file path finding (searches all locations)
3. Clear error messages when file not found
4. All existing functionality preserved

Version: 2.0.0 (Robust + better UX)
Date: February 13, 2026
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap
import cv2
from pathlib import Path
import os

from app.models.recording import Recording
from app.utils.logger import AppLogger
from config.app_config import RECORDINGS_DIR

logger = AppLogger("PlaybackScreen")


class PlaybackScreen(QWidget):
    """Video playback with robust file finding."""
    
    back_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.recording = None
        self.video_capture = None
        self.is_playing = False
        self.current_frame_number = 0
        self.total_frames = 0
        self.fps = 30
        self.playback_speed = 1.0
        
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback)
        
        self.init_ui()
        logger.info("Playback screen initialized")
    
    def init_ui(self):
        """Build UI with Back button at top-left."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # TOP BAR - Back button at LEFT (more intuitive)
        top_bar = QHBoxLayout()
        
        # CHANGED: Back button at TOP-LEFT (not top-right)
        back_btn = QPushButton("← Back to Library")
        back_btn.setFixedSize(180, 50)
        back_btn.setFont(QFont("Arial", 14, QFont.Bold))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:pressed { background-color: #7f8c8d; }
        """)
        back_btn.clicked.connect(self.on_back_clicked)
        top_bar.addWidget(back_btn)
        
        # Recording info - grows to fill space
        self.info_label = QLabel("No video loaded")
        self.info_label.setFont(QFont("Arial", 14))
        self.info_label.setStyleSheet("color: #2c3e50; padding-left: 20px;")
        top_bar.addWidget(self.info_label, stretch=1)
        
        main_layout.addLayout(top_bar)
        
        # VIDEO DISPLAY
        video_container = QFrame()
        video_container.setFrameStyle(QFrame.StyledPanel)
        video_container.setStyleSheet("QFrame { background-color: black; border: 2px solid #34495e; border-radius: 5px; }")
        video_container.setFixedSize(660, 500)
        
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(10, 10, 10, 10)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 18px;")
        self.video_label.setText("No video loaded")
        video_layout.addWidget(self.video_label)
        
        video_h_layout = QHBoxLayout()
        video_h_layout.addStretch()
        video_h_layout.addWidget(video_container)
        video_h_layout.addStretch()
        main_layout.addLayout(video_h_layout)
        
        # TIMELINE
        timeline_layout = QVBoxLayout()
        
        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.setValue(0)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7; height: 10px;
                background: #ecf0f1; border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #3498db; border: 1px solid #2980b9;
                width: 20px; margin: -5px 0; border-radius: 10px;
            }
        """)
        self.timeline_slider.sliderPressed.connect(self.on_timeline_pressed)
        self.timeline_slider.sliderReleased.connect(self.on_timeline_released)
        timeline_layout.addWidget(self.timeline_slider)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Arial", 14))
        timeline_layout.addWidget(self.time_label)
        
        main_layout.addLayout(timeline_layout)
        
        # CONTROLS
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.prev_frame_btn = self.create_button("◄◄", 80, 60)
        self.prev_frame_btn.clicked.connect(self.previous_frame)
        controls_layout.addWidget(self.prev_frame_btn)
        
        self.play_pause_btn = self.create_button("▶", 80, 60)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_pause_btn)
        
        self.stop_btn = self.create_button("■", 80, 60)
        self.stop_btn.clicked.connect(self.stop_playback)
        controls_layout.addWidget(self.stop_btn)
        
        self.next_frame_btn = self.create_button("►►", 80, 60)
        self.next_frame_btn.clicked.connect(self.next_frame)
        controls_layout.addWidget(self.next_frame_btn)
        
        controls_layout.addSpacing(40)
        
        speed_label = QLabel("Speed:")
        speed_label.setFont(QFont("Arial", 14, QFont.Bold))
        controls_layout.addWidget(speed_label)
        
        self.speed_05_btn = self.create_speed_button("0.5x", 0.5)
        controls_layout.addWidget(self.speed_05_btn)
        
        self.speed_1_btn = self.create_speed_button("1x", 1.0)
        controls_layout.addWidget(self.speed_1_btn)
        
        self.speed_2_btn = self.create_speed_button("2x", 2.0)
        controls_layout.addWidget(self.speed_2_btn)
        
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        
        self.set_controls_enabled(False)
    
    def create_button(self, text, width, height):
        """Create control button."""
        btn = QPushButton(text)
        btn.setFixedSize(width, height)
        btn.setFont(QFont("Arial", 18, QFont.Bold))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e; color: white;
                border: none; border-radius: 5px;
            }
            QPushButton:pressed { background-color: #2c3e50; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """)
        return btn
    
    def create_speed_button(self, text, speed):
        """Create speed button."""
        btn = QPushButton(text)
        btn.setFixedSize(60, 40)
        btn.setFont(QFont("Arial", 12, QFont.Bold))
        btn.setProperty("speed", speed)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6; color: white;
                border: none; border-radius: 5px;
            }
            QPushButton:pressed { background-color: #7f8c8d; }
        """)
        btn.clicked.connect(lambda: self.set_playback_speed(speed))
        return btn
    
    def load_video(self, recording: Recording):
        """
        Load video with ROBUST file finding.
        
        IMPROVEMENTS:
        1. Try database path first
        2. Try RECORDINGS_DIR
        3. Search all subdirectories
        4. Clear error messages if not found
        """
        if self.video_capture:
            self.video_capture.release()
        
        self.recording = recording
        
        # ROBUST FILE FINDING
        video_path = Path(recording.filepath)
        
        if not video_path.exists():
            logger.warning(f"File not at DB path: {recording.filepath}")
            
            # Try RECORDINGS_DIR
            video_path = Path(RECORDINGS_DIR) / recording.filename
            
            if not video_path.exists():
                logger.warning(f"File not in RECORDINGS_DIR")
                
                # Search all subdirectories
                for root, dirs, files in os.walk(RECORDINGS_DIR):
                    if recording.filename in files:
                        video_path = Path(root) / recording.filename
                        logger.info(f"✓ Found video at: {video_path}")
                        break
                else:
                    # NOT FOUND ANYWHERE
                    self.video_label.setText(
                        f"Video Not Found\n\n{recording.filename}\n\n"
                        "File may have been moved or deleted."
                    )
                    logger.error(f"✗ Video not found: {recording.filename}")
                    return
        
        # Open video
        self.video_capture = cv2.VideoCapture(str(video_path))
        
        if not self.video_capture.isOpened():
            self.video_label.setText("Failed to open video!")
            logger.error(f"Cannot open: {video_path}")
            return
        
        # Get properties
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS) or 30
        self.current_frame_number = 0
        
        self.timeline_slider.setMaximum(self.total_frames - 1)
        self.timeline_slider.setValue(0)
        
        # Update info
        patient = recording.patient_name or "No patient"
        procedure = recording.procedure_name or "No procedure"
        dur_m = recording.duration_seconds // 60
        dur_s = recording.duration_seconds % 60
        
        self.info_label.setText(f"Patient: {patient} | Procedure: {procedure} | Duration: {dur_m}:{dur_s:02d}")
        
        self.read_and_display_frame()
        self.set_controls_enabled(True)
        
        logger.info(f"✓ Video loaded: {recording.filename}")
    
    def set_controls_enabled(self, enabled):
        """Enable/disable controls."""
        self.play_pause_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.prev_frame_btn.setEnabled(enabled)
        self.next_frame_btn.setEnabled(enabled)
        self.timeline_slider.setEnabled(enabled)
    
    def toggle_play_pause(self):
        """Toggle play/pause."""
        if self.is_playing:
            self.pause_playback()
        else:
            self.play_playback()
    
    def play_playback(self):
        """Start playback."""
        if not self.video_capture:
            return
        self.is_playing = True
        self.play_pause_btn.setText("⏸")
        interval = int(1000 / (self.fps * self.playback_speed))
        self.playback_timer.start(interval)
    
    def pause_playback(self):
        """Pause."""
        self.is_playing = False
        self.play_pause_btn.setText("▶")
        self.playback_timer.stop()
    
    def stop_playback(self):
        """Stop and reset."""
        self.pause_playback()
        if self.video_capture:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_number = 0
            self.timeline_slider.setValue(0)
            self.read_and_display_frame()
    
    def previous_frame(self):
        """Previous frame."""
        if not self.video_capture:
            return
        self.pause_playback()
        if self.current_frame_number > 0:
            self.current_frame_number -= 1
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_number)
            self.read_and_display_frame()
    
    def next_frame(self):
        """Next frame."""
        if not self.video_capture:
            return
        self.pause_playback()
        if self.current_frame_number < self.total_frames - 1:
            self.current_frame_number += 1
            self.read_and_display_frame()
    
    def set_playback_speed(self, speed):
        """Set speed."""
        self.playback_speed = speed
        for btn in [self.speed_05_btn, self.speed_1_btn, self.speed_2_btn]:
            if btn.property("speed") == speed:
                btn.setStyleSheet(btn.styleSheet().replace("#95a5a6", "#3498db"))
            else:
                btn.setStyleSheet(btn.styleSheet().replace("#3498db", "#95a5a6"))
        if self.is_playing:
            self.pause_playback()
            self.play_playback()
    
    def on_timeline_pressed(self):
        """Timeline pressed."""
        self.pause_playback()
    
    def on_timeline_released(self):
        """Timeline released - seek."""
        if not self.video_capture:
            return
        frame_num = self.timeline_slider.value()
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        self.current_frame_number = frame_num
        self.read_and_display_frame()
    
    def update_playback(self):
        """Update playback."""
        if not self.video_capture or not self.is_playing:
            return
        if self.current_frame_number >= self.total_frames - 1:
            self.stop_playback()
            return
        self.read_and_display_frame()
    
    def read_and_display_frame(self):
        """Read and display frame."""
        if not self.video_capture:
            return
        
        ret, frame = self.video_capture.read()
        if not ret:
            return
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.video_label.setPixmap(pixmap)
        
        self.current_frame_number = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
        self.timeline_slider.setValue(self.current_frame_number)
        
        cur_sec = int(self.current_frame_number / self.fps)
        tot_sec = int(self.total_frames / self.fps)
        self.time_label.setText(f"{cur_sec//60:02d}:{cur_sec%60:02d} / {tot_sec//60:02d}:{tot_sec%60:02d}")
    
    def on_back_clicked(self):
        """Back to library."""
        self.pause_playback()
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        self.video_label.clear()
        self.video_label.setText("No video loaded")
        self.back_clicked.emit()
    
    def closeEvent(self, event):
        """Cleanup."""
        if self.video_capture:
            self.video_capture.release()
        super().closeEvent(event)


__all__ = ['PlaybackScreen']
