"""
Close Confirm Dialog - App Exit Handler

Handles the three scenarios when user clicks the red X:
  1. Recording in progress  → Warn, stay open
  2. Info dialog open       → Warn, stay open
  3. Clean state            → Confirm exit

Author: ZKB
Special Thanks: Dr. Farqaleet
Hospital: Lahore General Hospital - Eye Department
Version: 2.1.0
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from app.gui.recording.design_constants import (
    COLORS, get_button_style
)


class CloseConfirmDialog(QDialog):
    """
    Confirmation dialog for app close via red X button.

    Three scenarios:
    1. RECORDING_IN_PROGRESS: Shows warning, single OK button, stays open
    2. DIALOG_OPEN: Shows warning about open dialog, stays open
    3. CLEAN_STATE: Shows confirm with Cancel/Exit buttons

    Usage in main_window.py closeEvent:
        def closeEvent(self, event):
            result = CloseConfirmDialog.handle_close(
                parent=self,
                is_recording=self.recording_screen.is_recording(),
                is_dialog_open=self.recording_screen.is_dialog_open()
            )
            if result:
                event.accept()
            else:
                event.ignore()
    """

    # Dialog scenarios
    RECORDING_IN_PROGRESS = 'recording'
    DIALOG_OPEN = 'dialog'
    CLEAN_STATE = 'clean'

    def __init__(self, scenario, parent=None):
        """
        Initialize close confirm dialog.

        Args:
            scenario: One of RECORDING_IN_PROGRESS, DIALOG_OPEN, CLEAN_STATE
            parent: Parent widget
        """
        super().__init__(parent)
        self.scenario = scenario
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(380, 220)
        self._setup_ui()

    def _setup_ui(self):
        """Build dialog based on scenario."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
                border: 2px solid {COLORS['border_dark']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(15)

        if self.scenario == self.RECORDING_IN_PROGRESS:
            self._build_recording_warning(layout)
        elif self.scenario == self.DIALOG_OPEN:
            self._build_dialog_warning(layout)
        else:
            self._build_clean_confirm(layout)

    def _build_recording_warning(self, layout):
        """Warning: Cannot close while recording."""
        # Icon + Title
        title = QLabel("⚠  Cannot Close")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['danger']};")
        layout.addWidget(title)

        # Message
        msg = QLabel(
            "A recording is currently in progress.\n\n"
            "Please STOP the recording before\n"
            "closing the application."
        )
        msg.setFont(QFont("Arial", 11))
        msg.setStyleSheet(f"color: {COLORS['text_primary']};")
        msg.setWordWrap(True)
        layout.addWidget(msg)

        layout.addStretch()

        # Single OK button - returns to app
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("OK  - Return to App")
        ok_btn.setFixedSize(180, 42)
        ok_btn.setStyleSheet(get_button_style(
            COLORS['danger'], COLORS['danger_hover'], COLORS['danger_pressed'],
            font_size=12, radius=8
        ))
        ok_btn.clicked.connect(self.reject)  # Reject = stay in app
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def _build_dialog_warning(self, layout):
        """Warning: Cannot close while dialog is open."""
        # Icon + Title
        title = QLabel("⚠  Dialog Open")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['warning']};")
        layout.addWidget(title)

        # Message
        msg = QLabel(
            "A patient information dialog is\n"
            "currently open.\n\n"
            "Please close the dialog before\n"
            "exiting the application."
        )
        msg.setFont(QFont("Arial", 11))
        msg.setStyleSheet(f"color: {COLORS['text_primary']};")
        msg.setWordWrap(True)
        layout.addWidget(msg)

        layout.addStretch()

        # Single OK button - returns to app
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("OK  - Return to App")
        ok_btn.setFixedSize(180, 42)
        ok_btn.setStyleSheet(get_button_style(
            COLORS['warning'], COLORS['warning_hover'], COLORS['warning_hover'],
            font_size=12, radius=8
        ))
        ok_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def _build_clean_confirm(self, layout):
        """Standard exit confirmation."""
        # Icon + Title
        title = QLabel("Exit Application?")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(line)

        # Message
        msg = QLabel(
            "Are you sure you want to close\n"
            "OT Video Recording System?"
        )
        msg.setFont(QFont("Arial", 11))
        msg.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(msg)

        layout.addStretch()

        # Cancel and Exit buttons
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(110, 42)
        cancel_btn.setStyleSheet(get_button_style(
            COLORS['text_muted'], COLORS['border_dark'], COLORS['border_dark'],
            font_size=12, radius=8
        ))
        cancel_btn.clicked.connect(self.reject)  # Stay in app
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        exit_btn = QPushButton("Exit")
        exit_btn.setFixedSize(110, 42)
        exit_btn.setStyleSheet(get_button_style(
            COLORS['danger'], COLORS['danger_hover'], COLORS['danger_pressed'],
            font_size=12, radius=8
        ))
        exit_btn.clicked.connect(self.accept)  # Accept = exit app
        btn_layout.addWidget(exit_btn)

        layout.addLayout(btn_layout)

    @staticmethod
    def handle_close(parent, is_recording=False, is_dialog_open=False):
        """
        Static helper - determine scenario and show appropriate dialog.

        Args:
            parent: Parent widget
            is_recording: True if recording is in progress
            is_dialog_open: True if metadata/info dialog is open

        Returns:
            bool: True if app should close, False if should stay open

        Usage:
            result = CloseConfirmDialog.handle_close(
                parent=self,
                is_recording=self.recording_screen.is_recording(),
                is_dialog_open=self.recording_screen.is_dialog_open()
            )
            if result:
                event.accept()
            else:
                event.ignore()
        """
        if is_recording:
            # Scenario 1: Recording in progress - cannot close
            dlg = CloseConfirmDialog(
                CloseConfirmDialog.RECORDING_IN_PROGRESS, parent
            )
            dlg.exec_()
            return False  # Always stay open

        elif is_dialog_open:
            # Scenario 2: Dialog open - cannot close
            dlg = CloseConfirmDialog(
                CloseConfirmDialog.DIALOG_OPEN, parent
            )
            dlg.exec_()
            return False  # Always stay open

        else:
            # Scenario 3: Clean state - ask to confirm
            dlg = CloseConfirmDialog(
                CloseConfirmDialog.CLEAN_STATE, parent
            )
            result = dlg.exec_()
            return result == QDialog.Accepted  # True=exit, False=stay
