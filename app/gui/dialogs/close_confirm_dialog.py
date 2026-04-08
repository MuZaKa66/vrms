"""
Close Confirm Dialog - App Exit Handler

Handles the three scenarios when user clicks the red X:
  1. Recording in progress  → Warn, stay open
  2. Info dialog open       → Warn, stay open
  3. Clean state            → Confirm exit

FONT/SIZE CONSTANTS: All controlled via app_config.py
  MSGBOX_FONT_SIZE    — title font size
  MSGBOX_MSG_FONT     — message body font size
  MSGBOX_BTN_FONT     — button label font size
  MSGBOX_BTN_WIDTH    — button minimum width
  MSGBOX_BTN_HEIGHT   — button minimum height

Author: ZKB
Hospital: Lahore General Hospital - Eye Department
Version: 2.2.0
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

from app.gui.recording.design_constants import COLORS, get_button_style
from config.app_config import (
    MSGBOX_FONT_SIZE, MSGBOX_MSG_FONT,
    MSGBOX_BTN_FONT, MSGBOX_BTN_WIDTH, MSGBOX_BTN_HEIGHT
)

# Dialog size — scales with font
DIALOG_W = 460
DIALOG_H = 280


class CloseConfirmDialog(QDialog):
    """
    Confirmation dialog for app close via red X button.
    All font sizes and button dimensions driven by app_config constants.
    """

    RECORDING_IN_PROGRESS = 'recording'
    DIALOG_OPEN           = 'dialog'
    CLEAN_STATE           = 'clean'

    def __init__(self, scenario, parent=None):
        super().__init__(parent)
        self.scenario = scenario
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(DIALOG_W, DIALOG_H)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
                border: 2px solid {COLORS['border_dark']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        if self.scenario == self.RECORDING_IN_PROGRESS:
            self._build_recording_warning(layout)
        elif self.scenario == self.DIALOG_OPEN:
            self._build_dialog_warning(layout)
        else:
            self._build_clean_confirm(layout)

    def _title(self, text, color):
        """Create title label."""
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", MSGBOX_FONT_SIZE, QFont.Bold))
        lbl.setStyleSheet(f"color: {color};")
        return lbl

    def _msg(self, text):
        """Create message body label."""
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", MSGBOX_MSG_FONT))
        lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        lbl.setWordWrap(True)
        return lbl

    def _btn(self, text, bg, hover, pressed):
        """Create action button."""
        btn = QPushButton(text)
        btn.setFixedSize(MSGBOX_BTN_WIDTH, MSGBOX_BTN_HEIGHT)
        btn.setStyleSheet(get_button_style(
            bg, hover, pressed,
            font_size=MSGBOX_BTN_FONT, radius=8
        ))
        return btn

    def _build_recording_warning(self, layout):
        layout.addWidget(self._title("Cannot Close", COLORS['danger']))
        layout.addWidget(self._msg(
            "A recording is currently in progress.\n\n"
            "Please STOP the recording before closing."
        ))
        layout.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        ok = self._btn("OK - Return to App",
                       COLORS['danger'], COLORS['danger_hover'],
                       COLORS['danger_pressed'])
        ok.clicked.connect(self.reject)
        row.addWidget(ok)
        layout.addLayout(row)

    def _build_dialog_warning(self, layout):
        layout.addWidget(self._title("Dialog Open", COLORS['warning']))
        layout.addWidget(self._msg(
            "A patient information dialog is currently open.\n\n"
            "Please close the dialog before exiting."
        ))
        layout.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        ok = self._btn("OK - Return to App",
                       COLORS['warning'], COLORS['warning_hover'],
                       COLORS['warning_hover'])
        ok.clicked.connect(self.reject)
        row.addWidget(ok)
        layout.addLayout(row)

    def _build_clean_confirm(self, layout):
        layout.addWidget(self._title("Exit Application?",
                                     COLORS['text_primary']))

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(line)

        layout.addWidget(self._msg(
            "Are you sure you want to close (VRMS)\n"
            " Video Recording Management System?"
        ))
        layout.addStretch()

        row = QHBoxLayout()
        cancel = self._btn("Cancel",
                           COLORS['text_muted'], COLORS['border_dark'],
                           COLORS['border_dark'])
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        row.addStretch()
        exit_btn = self._btn("Exit",
                             COLORS['danger'], COLORS['danger_hover'],
                             COLORS['danger_pressed'])
        exit_btn.clicked.connect(self.accept)
        row.addWidget(exit_btn)
        layout.addLayout(row)

    @staticmethod
    def handle_close(parent, is_recording=False, is_dialog_open=False):
        if is_recording:
            dlg = CloseConfirmDialog(
                CloseConfirmDialog.RECORDING_IN_PROGRESS, parent)
            dlg.exec_()
            return False
        elif is_dialog_open:
            dlg = CloseConfirmDialog(
                CloseConfirmDialog.DIALOG_OPEN, parent)
            dlg.exec_()
            return False
        else:
            dlg = CloseConfirmDialog(
                CloseConfirmDialog.CLEAN_STATE, parent)
            return dlg.exec_() == QDialog.Accepted
