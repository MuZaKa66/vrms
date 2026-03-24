"""
UI Builder - Component Creation and Layout

Handles all UI component creation and layout for Recording Screen.
Separates UI construction from business logic for better maintainability.

All components use design tokens from design_constants.py for consistency.

Author: OT Video Dev Team
Date: February 16, 2026  
Version: 2.0.0 (Refactored - BLACK STRIP BUGS FIXED)
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QColor

from .design_constants import (
    SPACING, COLORS, SIZES,
    get_info_button_style, get_record_button_style
)


class UIBuilder:
    """
    Builds UI components for Recording Screen.
    
    All components follow the design system defined in design_constants.py.
    This class is stateless - it just creates and returns widgets.
    """
    
    @staticmethod
    def create_storage_bar():
        """
        Create storage usage indicator bar.
        
        Returns:
            tuple: (frame, storage_bar_widget)
                - frame: Container QFrame
                - storage_bar_widget: QProgressBar for updating
        
        Example:
            >>> frame, bar = UIBuilder.create_storage_bar()
            >>> bar.setValue(75)  # Set to 75% used
            >>> bar.setFormat("75% used (50 GB free)")
        """
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background-color: {COLORS['background']}; border-radius: 5px; }}")
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # "Storage:" label
        label = QLabel("Storage:")
        label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(label)
        
        # Progress bar
        storage_bar = QProgressBar()
        storage_bar.setMinimum(0)
        storage_bar.setMaximum(100)
        storage_bar.setValue(0)
        storage_bar.setFormat("Calculating...")
        storage_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {COLORS['background_dark']};
                border-radius: 5px;
                text-align: center;
                height: 30px;
            }}
            QProgressBar::chunk {{ background-color: {COLORS['success']}; }}
        """)
        
        layout.addWidget(storage_bar)
        
        return frame, storage_bar
    
    @staticmethod
    def create_status_label():
        """
        Create status label ("Ready to Record", "Recording in Progress", etc.).
        
        Returns:
            QLabel: Status label widget
        """
        label = QLabel("Ready to Record")
        label.setFont(QFont("Arial", SIZES['font_status'], QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {COLORS['danger']};")
        return label
    
    @staticmethod
    def create_timer_label():
        """
        Create recording timer label (00:00:00).
        
        Returns:
            QLabel: Timer label widget
        """
        label = QLabel("00:00:00")
        label.setFont(QFont("Arial", SIZES['font_timer'], QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {COLORS['text_primary']};")
        return label
    
    @staticmethod
    def create_info_button(has_info=False):
        """
        Create Add/Edit Info button.
        
        Args:
            has_info: True for "Edit Info", False for "Add Info"
        
        Returns:
            QPushButton: Info button widget
        
        Example:
            >>> btn = UIBuilder.create_info_button(has_info=False)
            >>> btn.setText("Add Info")
        """
        button = QPushButton("Add Info")
        button.setFixedSize(SIZES['info_button'][0], SIZES['info_button'][1])
        button.setStyleSheet(get_info_button_style(has_info))
        return button
    
    @staticmethod
    def create_clear_button():
        """
        Create Clear button (for clearing info).
        
        Returns:
            QPushButton: Clear button widget (initially hidden)
        """
        button = QPushButton("Clear")
        button.setFixedSize(100, SIZES['info_button'][1])
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['text_secondary']};
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLORS['border']}; }}
        """)
        button.setVisible(False)  # Hidden by default
        return button
    
    @staticmethod
    def create_info_display_label():
        """
        Create info display label (shows "Patient: John Doe").
        
        Returns:
            QLabel: Info display label widget
        """
        label = QLabel("")
        label.setFont(QFont("Arial", SIZES['font_label']))
        label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        label.setWordWrap(True)
        return label
    
    @staticmethod
    def create_record_button(is_recording=False):
        """
        Create START/STOP recording button.
        
        Args:
            is_recording: True for "STOP RECORDING", False for "START RECORDING"
        
        Returns:
            QPushButton: Record button widget
        
        Example:
            >>> btn = UIBuilder.create_record_button(is_recording=False)
            >>> # Later when recording starts:
            >>> btn.setText("STOP RECORDING")
            >>> btn.setStyleSheet(get_record_button_style(is_recording=True))
        """
        button = QPushButton("START RECORDING")
        button.setFixedSize(SIZES['record_button'][0], SIZES['record_button'][1])
        # CRITICAL FIX: Removed setMinimumSize and setMaximumSize
        # They conflict with setFixedSize and caused button height issues
        button.setStyleSheet(get_record_button_style(is_recording))
        return button
    
    @staticmethod
    def create_preview_container():
        """
        Create preview container with recording indicator and video preview.
        
        CRITICAL FIXES APPLIED:
        - Removed setMinimumSize/setMaximumSize from preview_label
        - Only using setFixedSize to prevent black strip collapse
        
        Returns:
            tuple: (container, preview_label, recording_indicator, preview_buffer)
                - container: QFrame containing everything
                - preview_label: QLabel for video display
                - recording_indicator: QLabel for "● Recording" text
                - preview_buffer: QPixmap for double buffering
        
        Example:
            >>> container, label, indicator, buffer = UIBuilder.create_preview_container()
            >>> # Later: Update preview
            >>> label.setPixmap(buffer)
        """
        container = QFrame()
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 10, 0)  # Right margin only
        layout.setSpacing(3)
        
        # Recording indicator ("● Recording" text)
        recording_indicator = QLabel()
        recording_indicator.setFont(QFont("Arial", 10, QFont.Bold))
        recording_indicator.setTextFormat(Qt.RichText)
        recording_indicator.setText("")  # Initially hidden
        recording_indicator.setAlignment(Qt.AlignLeft)
        layout.addWidget(recording_indicator)
        
        # Preview label (video display area)
        preview_label = QLabel()
        preview_size = SIZES['preview']
        
        # CRITICAL FIX: Only use setFixedSize, NO setMinimumSize/setMaximumSize
        # The min/max calls conflict with setFixedSize and cause Qt to ignore
        # the fixed size, allowing the widget to collapse to a black strip
        preview_label.setFixedSize(preview_size[0], preview_size[1])
        
        preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['preview_bg']};
                border: 2px solid {COLORS['border']};
                border-radius: 5px;
                color: {COLORS['text_light']};
            }}
        """)
        preview_label.setAlignment(Qt.AlignCenter)
        
        # Initialize preview buffer for double-buffered rendering
        preview_buffer = QPixmap(preview_size[0], preview_size[1])
        preview_buffer.fill(QColor(COLORS['preview_bg']))
        preview_label.setPixmap(preview_buffer)
        
        layout.addWidget(preview_label)
        
        # CRITICAL FIX: Fix container size to prevent any collapse
        container.setFixedSize(
            preview_size[0] + 10,   # Width + right margin
            preview_size[1] + 25    # Height + indicator label height
        )
        
        return container, preview_label, recording_indicator, preview_buffer
    
    @staticmethod
    def update_recording_indicator(indicator_label, visible=True):
        """
        Update recording indicator visibility and animation.
        
        Args:
            indicator_label: QLabel widget for "● Recording" text
            visible: True to show dot, False to hide
        
        Example:
            >>> # Show indicator
            >>> UIBuilder.update_recording_indicator(label, visible=True)
            >>> # Hide indicator (dot blinks off)
            >>> UIBuilder.update_recording_indicator(label, visible=False)
        """
        if visible:
            # Show red dot with "Recording" text
            indicator_label.setText(
                f'<span style="color: {COLORS["danger"]};">●</span> '
                f'<span style="color: {COLORS["danger"]};">Recording</span>'
            )
        else:
            # Hide dot (space maintains layout)
            indicator_label.setText(
                f'<span style="color: transparent;">●</span> '
                f'<span style="color: {COLORS["danger"]};">Recording</span>'
            )


__all__ = ['UIBuilder']
