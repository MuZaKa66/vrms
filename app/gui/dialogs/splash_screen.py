"""
Splash Screen - Shown on Every Application Launch

Displays hospital branding and brief disclaimer notice.
Auto-dismisses after 3 seconds or on tap/click.

Author: ZKB
Special Thanks: Dr. Farqaleet
Hospital: Lahore General Hospital - Eye Department
Version: 2.1.0
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from app.gui.recording.design_constants import (
    COLORS, SIZES, TIMINGS, LOGO_PATH
)


class SplashScreen(QDialog):
    """
    Startup splash screen shown on every launch.

    Displays:
    - LGH logo
    - App name
    - Brief disclaimer notice
    - Auto-dismiss countdown

    Dismissed by:
    - Clicking anywhere
    - 3 second auto-dismiss timer
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Dialog |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setModal(True)
        self.setFixedSize(420, 340)
        self._setup_ui()
        self._start_timer()

    def _setup_ui(self):
        """Build splash screen layout."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background_dark']};
                border: 3px solid {COLORS['success']};
                border-radius: 15px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        # ── Logo ────────────────────────────────────────────────────────
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(LOGO_PATH):
            pixmap = QPixmap(LOGO_PATH)
            pixmap = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("🏥")
            logo_label.setFont(QFont("Arial", 40))
        layout.addWidget(logo_label)

        # ── Hospital Name ────────────────────────────────────────────────
        hospital_label = QLabel("Lahore General Hospital")
        hospital_label.setFont(QFont("Arial", 16, QFont.Bold))
        hospital_label.setAlignment(Qt.AlignCenter)
        hospital_label.setStyleSheet(f"color: {COLORS['text_light']};")
        layout.addWidget(hospital_label)

        # ── Department ───────────────────────────────────────────────────
        dept_label = QLabel("Eye Department")
        dept_label.setFont(QFont("Arial", 12))
        dept_label.setAlignment(Qt.AlignCenter)
        dept_label.setStyleSheet(f"color: {COLORS['success']};")
        layout.addWidget(dept_label)

        # ── Divider ──────────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {COLORS['border_dark']};")
        layout.addWidget(line)

        # ── App Name ─────────────────────────────────────────────────────
        app_label = QLabel("OT Video Recording System")
        app_label.setFont(QFont("Arial", 13, QFont.Bold))
        app_label.setAlignment(Qt.AlignCenter)
        app_label.setStyleSheet(f"color: {COLORS['info']};")
        layout.addWidget(app_label)

        # ── Disclaimer Notice ────────────────────────────────────────────
        disclaimer_label = QLabel("⚠  For Documentation & Educational Use Only")
        disclaimer_label.setFont(QFont("Arial", 11))
        disclaimer_label.setAlignment(Qt.AlignCenter)
        disclaimer_label.setStyleSheet(f"color: {COLORS['warning']};")
        layout.addWidget(disclaimer_label)

        notice_label = QLabel("Not a certified medical device")
        notice_label.setFont(QFont("Arial", 10))
        notice_label.setAlignment(Qt.AlignCenter)
        notice_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(notice_label)

        # ── Tap to continue ──────────────────────────────────────────────
        self.continue_label = QLabel("Tap anywhere to continue  (3)")
        self.continue_label.setFont(QFont("Arial", 10))
        self.continue_label.setAlignment(Qt.AlignCenter)
        self.continue_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.continue_label)

        # ── Countdown ────────────────────────────────────────────────────
        self.countdown = 3
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._tick)
        self.countdown_timer.start(1000)

    def _start_timer(self):
        """Auto-dismiss after splash duration."""
        QTimer.singleShot(TIMINGS['splash_duration'], self.accept)

    def _tick(self):
        """Update countdown label each second."""
        self.countdown -= 1
        if self.countdown > 0:
            self.continue_label.setText(
                f"Tap anywhere to continue  ({self.countdown})"
            )
        else:
            self.countdown_timer.stop()

    def mousePressEvent(self, event):
        """Dismiss on tap/click anywhere."""
        self.accept()

    def keyPressEvent(self, event):
        """Dismiss on any key press."""
        self.accept()
