"""
Disclaimer Dialog - First Launch Acceptance

Shown ONLY on first launch. Requires explicit acceptance.
Records acceptance with timestamp to config/acceptance.txt.
Never shown again after acceptance.

Author: ZKB
Special Thanks: Dr. Farqaleet
Hospital: Lahore General Hospital - Eye Department
Version: 2.1.0
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from app.gui.recording.design_constants import (
    COLORS, SIZES, LOGO_PATH,
    save_acceptance, get_button_style
)


class DisclaimerDialog(QDialog):
    """
    First-launch disclaimer and terms acceptance dialog.

    Shows:
    - Full disclaimer text
    - Classification notice (Class I device)
    - Liability disclaimer
    - Intended use statement
    - Accept button (required to proceed)

    On acceptance:
    - Writes config/acceptance.txt
    - Dialog closes
    - App continues to main window

    On rejection/close:
    - App exits (cannot use without acceptance)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OT Video System - Terms of Use")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setModal(True)
        self.setFixedSize(560, 640)
        self._setup_ui()

    def _setup_ui(self):
        """Build disclaimer dialog layout."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header Bar ───────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(90)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['status_bar_bg']};
                border-bottom: 3px solid {COLORS['success']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        # Logo in header
        logo_label = QLabel()
        if os.path.exists(LOGO_PATH):
            pixmap = QPixmap(LOGO_PATH)
            pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        header_layout.addWidget(logo_label)

        # Hospital name
        header_text = QVBoxLayout()
        hosp_label = QLabel("Lahore General Hospital")
        hosp_label.setFont(QFont("Arial", 14, QFont.Bold))
        hosp_label.setStyleSheet(f"color: {COLORS['text_light']};")
        dept_label = QLabel("Eye Department - OT Video Recording System")
        dept_label.setFont(QFont("Arial", 10))
        dept_label.setStyleSheet(f"color: {COLORS['success']};")
        header_text.addWidget(hosp_label)
        header_text.addWidget(dept_label)
        header_layout.addLayout(header_text)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # ── Scroll Area for Disclaimer Text ──────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['background']};
            }}
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 20, 25, 20)
        content_layout.setSpacing(15)

        # Title
        title = QLabel("DISCLAIMER & DECLARATION OF USE")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['danger']};")
        content_layout.addWidget(title)

        # Classification notice
        class_frame = QFrame()
        class_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_card']};
                border: 2px solid {COLORS['success']};
                border-radius: 8px;
                padding: 5px;
            }}
        """)
        class_layout = QVBoxLayout(class_frame)
        class_layout.setContentsMargins(12, 10, 12, 10)

        class_title = QLabel("Device Classification")
        class_title.setFont(QFont("Arial", 11, QFont.Bold))
        class_title.setStyleSheet(f"color: {COLORS['success']};")
        class_layout.addWidget(class_title)

        class_text = QLabel(
            "This system is classified as a Class I Medical Documentation Tool.\n"
            "It poses minimal risk and has no direct impact on patient safety."
        )
        class_text.setFont(QFont("Arial", 10))
        class_text.setWordWrap(True)
        class_text.setStyleSheet(f"color: {COLORS['text_primary']};")
        class_layout.addWidget(class_text)
        content_layout.addWidget(class_frame)

        # Intended use
        self._add_section(
            content_layout,
            "✓  Intended Use",
            "• Surgical procedure documentation and archiving\n"
            "• Medical education and surgical training\n"
            "• Clinical reference and case review\n"
            "• Departmental quality assurance",
            COLORS['success']
        )

        # NOT intended for
        self._add_section(
            content_layout,
            "✗  This System is NOT:",
            "• A substitute for clinical judgment or medical expertise\n"
            "• A diagnostic or therapeutic tool\n"
            "• A life-support or safety-critical system\n"
            "• An official or legal medical record system\n"
            "• DRAP registered or formally certified",
            COLORS['danger']
        )

        # Liability disclaimer
        self._add_section(
            content_layout,
            "⚠  Liability Disclaimer",
            "The Department of Surgery, Lahore General Hospital and the "
            "system developers (ZKB) assume NO liability for:\n\n"
            "• Recording failures, data loss, or corruption\n"
            "• Clinical decisions based on recorded material\n"
            "• Misuse or unauthorized use of recorded content\n"
            "• Patient privacy breaches due to unauthorized access\n"
            "• Any direct or indirect consequences of system use",
            COLORS['warning']
        )

        # User responsibility
        self._add_section(
            content_layout,
            "📋  By Accepting You Confirm:",
            "• You are authorized personnel of LGH Eye Department\n"
            "• You understand the limitations of this system\n"
            "• All clinical decisions remain your sole responsibility\n"
            "• You will use recordings responsibly and ethically\n"
            "• Patient consent for recording is your responsibility",
            COLORS['info']
        )

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # ── Footer with Accept Button ─────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(75)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_card']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 12, 20, 12)

        exit_btn = QPushButton("Exit")
        exit_btn.setFixedSize(100, 44)
        exit_btn.setStyleSheet(get_button_style(
            COLORS['text_muted'], COLORS['border_dark'], COLORS['border_dark'],
            font_size=13, radius=8
        ))
        exit_btn.clicked.connect(self.reject)
        footer_layout.addWidget(exit_btn)

        footer_layout.addStretch()

        accept_btn = QPushButton("I Understand and Accept")
        accept_btn.setFixedSize(220, 44)
        accept_btn.setStyleSheet(get_button_style(
            COLORS['success'], COLORS['success_hover'], COLORS['success_pressed'],
            font_size=13, radius=8
        ))
        accept_btn.clicked.connect(self._on_accept)
        footer_layout.addWidget(accept_btn)

        main_layout.addWidget(footer)

    def _add_section(self, layout, title, text, color):
        """Helper to add a styled disclaimer section."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_card']};
                border-left: 4px solid {color};
                border-radius: 4px;
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(12, 10, 12, 10)
        frame_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setStyleSheet(f"color: {color}; border: none;")
        frame_layout.addWidget(title_label)

        text_label = QLabel(text)
        text_label.setFont(QFont("Arial", 10))
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        frame_layout.addWidget(text_label)

        layout.addWidget(frame)

    def _on_accept(self):
        """Save acceptance and close dialog."""
        success, error = save_acceptance()
        if success:
            self.accept()
        else:
            # Even if save fails, allow proceeding
            self.accept()
