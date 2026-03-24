"""
About Dialog - App Info, Branding and Credits

Shows hospital branding, version info, developer credits,
acceptance date and full disclaimer link.

Author: ZKB
Special Thanks: Dr. Farqaleet
Hospital: Lahore General Hospital - Eye Department
Version: 2.1.0
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))))

from app.gui.recording.design_constants import (
    COLORS, LOGO_PATH, get_button_style,
    get_acceptance_date
)


APP_VERSION = "2.1.0"
BUILD_DATE = "February 2026"


class AboutDialog(QDialog):
    """
    About dialog showing hospital branding and app information.

    Displays:
    - LGH logo and hospital name
    - Eye Department
    - App version and build date
    - Developer credits (ZKB)
    - Special thanks (Dr. Farqaleet)
    - Classification notice
    - Disclaimer acceptance date
    - Link to view full disclaimer
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About - OT Video Recording System")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setFixedSize(420, 540)
        self._setup_ui()

    def _setup_ui(self):
        """Build about dialog layout."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(130)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['status_bar_bg']};
                border-bottom: 3px solid {COLORS['success']};
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(5)

        # Logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(LOGO_PATH):
            pixmap = QPixmap(LOGO_PATH)
            pixmap = pixmap.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("🏥")
            logo_label.setFont(QFont("Arial", 35))
            logo_label.setStyleSheet(f"color: {COLORS['text_light']};")
        header_layout.addWidget(logo_label)

        # Hospital name
        hosp_name = QLabel("Lahore General Hospital")
        hosp_name.setFont(QFont("Arial", 14, QFont.Bold))
        hosp_name.setAlignment(Qt.AlignCenter)
        hosp_name.setStyleSheet(f"color: {COLORS['text_light']};")
        header_layout.addWidget(hosp_name)

        layout.addWidget(header)

        # ── Content ──────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 20, 25, 15)
        content_layout.setSpacing(12)

        # App info
        self._add_info_row(content_layout, "Application",
                           "OT Video Recording System")
        self._add_info_row(content_layout, "Department",
                           "Eye Department")
        self._add_info_row(content_layout, "Version",
                           f"v{APP_VERSION}  ({BUILD_DATE})")
        self._add_info_row(content_layout, "Platform",
                           "Raspberry Pi 4B / Windows")
        self._add_info_row(content_layout, "Classification",
                           "Class I - Documentation Tool")

        # Divider
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet(f"color: {COLORS['border']};")
        content_layout.addWidget(line1)

        # Credits
        dev_label = QLabel("Development & Credits")
        dev_label.setFont(QFont("Arial", 11, QFont.Bold))
        dev_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        content_layout.addWidget(dev_label)

        self._add_info_row(content_layout, "Developer", "ZKB")
        self._add_info_row(content_layout, "Special Thanks",
                           "Dr. Farqaleet")
        self._add_info_row(content_layout, "Assistance",
                           "LGH Eye Department Team")

        # Divider
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet(f"color: {COLORS['border']};")
        content_layout.addWidget(line2)

        # Disclaimer acceptance
        acceptance_date = get_acceptance_date()
        self._add_info_row(content_layout, "Terms Accepted", acceptance_date)

        # Copyright
        copy_label = QLabel("© 2026 Lahore General Hospital\nAll Rights Reserved")
        copy_label.setFont(QFont("Arial", 9))
        copy_label.setAlignment(Qt.AlignCenter)
        copy_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        content_layout.addWidget(copy_label)

        content_layout.addStretch()
        layout.addWidget(content)

        # ── Footer ───────────────────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(65)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_card']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)

        disclaimer_btn = QPushButton("View Disclaimer")
        disclaimer_btn.setFixedSize(140, 38)
        disclaimer_btn.setStyleSheet(get_button_style(
            COLORS['info'], COLORS['info_hover'], COLORS['info_pressed'],
            font_size=11, radius=8
        ))
        disclaimer_btn.clicked.connect(self._show_disclaimer)
        footer_layout.addWidget(disclaimer_btn)

        footer_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 38)
        close_btn.setStyleSheet(get_button_style(
            COLORS['success'], COLORS['success_hover'], COLORS['success_pressed'],
            font_size=12, radius=8
        ))
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)

    def _add_info_row(self, layout, label_text, value_text):
        """Add a label: value row to the layout."""
        row = QHBoxLayout()
        row.setSpacing(10)

        label = QLabel(f"{label_text}:")
        label.setFont(QFont("Arial", 10, QFont.Bold))
        label.setFixedWidth(120)
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        row.addWidget(label)

        value = QLabel(value_text)
        value.setFont(QFont("Arial", 10))
        value.setStyleSheet(f"color: {COLORS['text_primary']};")
        value.setWordWrap(True)
        row.addWidget(value, 1)

        layout.addLayout(row)

    def _show_disclaimer(self):
        """Show full disclaimer dialog for reference."""
        from app.gui.dialogs.disclaimer_dialog import DisclaimerDialog
        dlg = DisclaimerDialog(self)
        dlg.exec_()
