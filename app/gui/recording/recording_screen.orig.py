"""
Recording Screen - Main Orchestrator

Main controller for the recording interface.
Coordinates all components: UI, preview, recording, metadata.

REFACTORED STRUCTURE (v2.0.0):
- Was: 1400+ lines monolithic file
- Now: 400 lines orchestrator + 6 specialized modules

Components:
- design_constants.py: Design system (colors, sizes, spacing)
- ui_builder.py: UI component creation
- preview_handler.py: Video preview rendering
- recording_controller_wrapper.py: Recording state management
- metadata_handler.py: Patient info management
- recording_screen.py: This file - orchestrates everything

Author: OT Video Dev Team
Date: February 16, 2026
Version: 2.0.0 (Refactored)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QTimer, Qt

from app.utils.logger import AppLogger

# Import refactored components
from .design_constants import SPACING, COLORS, TIMINGS
from .ui_builder import UIBuilder
from .preview_handler import PreviewHandler
from .recording_controller_wrapper import RecordingControllerWrapper, RecordingTimer
from .metadata_handler import MetadataHandler

logger = AppLogger("RecordingScreen")


class RecordingScreen(QWidget):
    """
    Main recording screen interface.
    
    ARCHITECTURE:
    - Thin orchestration layer
    - Delegates to specialized components
    - Coordinates component interactions
    - Handles high-level workflows
    
    COMPONENTS:
    - UIBuilder: Creates all UI widgets
    - PreviewHandler: Manages video preview
    - RecordingControllerWrapper: Handles recording operations
    - RecordingTimer: Updates timer display
    - MetadataHandler: Manages patient info
    - StorageService: Monitors disk space
    
    WORKFLOWS:
    1. Start recording → Update UI → Start preview → Start timer
    2. Stop recording → Stop timer → Stop preview → Save metadata
    3. Add info → Show dialog → Update display
    4. Voice command → Silent workflow
    """
    
    def __init__(self, parent=None):
        """
        Initialize recording screen.
        
        Creates all components and connects signals.
        """
        super().__init__(parent)
        
        # Component instances (created in init_ui)
        self.preview_handler = None
        self.recording_wrapper = None
        self.recording_timer = None
        self.metadata_handler = None
        
        # State
        self.voice_mode_active = False
        
        # Timers
        self.storage_check_timer = QTimer()
        self.dot_blink_timer = QTimer()
        self.preview_update_timer = QTimer()
        self.dot_visible = True
        
        # Build UI
        self._init_ui()
        
        # Setup timers
        self._setup_timers()
        
        # Initial storage check
        self._update_storage_display()
        
        logger.info("RecordingScreen initialized (Refactored v2.0)")
    
    def _init_ui(self):
        """
        Build complete user interface.
        
        Uses UIBuilder for component creation.
        Assembles components into final layout.
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(SPACING['sm'])
        main_layout.setContentsMargins(
            SPACING['md'],
            SPACING['sm'],
            SPACING['md'],
            SPACING['lg']
        )
        
        # === STORAGE BAR ===
        storage_frame, self.storage_bar = UIBuilder.create_storage_bar()
        main_layout.addWidget(storage_frame)
        
        main_layout.addSpacing(SPACING['xs'])
        
        # === STATUS LABEL ===
        self.status_label = UIBuilder.create_status_label()
        main_layout.addWidget(self.status_label)
        
        # === INFO ROW ===
        info_row = QHBoxLayout()
        info_row.setSpacing(SPACING['md'])
        
        # Buttons
        self.info_btn = UIBuilder.create_info_button(has_info=False)
        self.info_btn.clicked.connect(self._on_info_button_clicked)
        info_row.addWidget(self.info_btn)
        
        self.clear_btn = UIBuilder.create_clear_button()
        self.clear_btn.clicked.connect(self._on_clear_button_clicked)
        info_row.addWidget(self.clear_btn)
        
        # Info display
        self.info_display = UIBuilder.create_info_display_label()
        info_row.addWidget(self.info_display, 1)
        
        main_layout.addLayout(info_row)
        
        # === TIMER ===
        main_layout.addSpacing(SPACING['xs'])
        
        self.timer_label = UIBuilder.create_timer_label()
        main_layout.addWidget(self.timer_label)
        
        main_layout.addSpacing(SPACING['xs'])
        
        # === PREVIEW CONTAINER ===
        (preview_container, 
         self.preview_label, 
         self.recording_indicator,
         preview_buffer) = UIBuilder.create_preview_container()
        
        # CRITICAL FIX: Remove stretch factor 0 that was causing black strip
        main_layout.addWidget(preview_container, alignment=Qt.AlignRight)
        
        # === RECORD BUTTON ===
        main_layout.addSpacing(SPACING['sm'])
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.record_btn = UIBuilder.create_record_button(is_recording=False)
        self.record_btn.clicked.connect(self._on_record_button_clicked)
        button_layout.addWidget(self.record_btn)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Bottom spacing (separation from nav bar)
        main_layout.addSpacing(SPACING['xxl'])
        
        # === INITIALIZE COMPONENTS ===
        
        # Preview handler
        self.preview_handler = PreviewHandler(
            self.preview_label,
            preview_buffer,
            None,  # Will be set when recording wrapper is created
            throttle=TIMINGS['preview_throttle']
        )
        
        # Recording wrapper
        self.recording_wrapper = RecordingControllerWrapper(
            on_state_change=self._on_recording_state_change,
            on_error=self._on_recording_error
        )
        
        # Connect controller to preview
        self.preview_handler.controller = self.recording_wrapper.controller
        
        # Recording timer
        self.recording_timer = RecordingTimer(
            self.timer_label,
            self.recording_wrapper
        )
        
        # Metadata handler
        self.metadata_handler = MetadataHandler(
            self.info_display,
            self.info_btn,
            self.clear_btn,
            self
        )
    
    def _setup_timers(self):
        """Setup all periodic timers."""
        # Storage check (every 30 seconds)
        self.storage_check_timer.timeout.connect(self._update_storage_display)
        self.storage_check_timer.start(TIMINGS['storage_check'])
        
        # Preview update (every 100ms when recording)
        self.preview_update_timer.timeout.connect(self.preview_handler.update_preview)
        
        # Dot blink (every 500ms when recording)
        self.dot_blink_timer.timeout.connect(self._toggle_recording_indicator)
        
        logger.debug("Timers configured")
    
    # =========================================================================
    # BUTTON CLICK HANDLERS
    # =========================================================================
    
    def _on_info_button_clicked(self):
        """Handle Add/Edit Info button click."""
        result = self.metadata_handler.show_metadata_dialog(recording=None)
        if result:
            self.status_label.setText("✓ Info Added - Ready to Record")
    
    def _on_clear_button_clicked(self):
        """Handle Clear button click."""
        self.metadata_handler.confirm_clear()
    
    def _on_record_button_clicked(self):
        """Handle START/STOP recording button click."""
        from app.utils.constants import RecordingState
        
        if self.recording_wrapper.state == RecordingState.IDLE:
            self._start_recording()
        elif self.recording_wrapper.state == RecordingState.RECORDING:
            self._stop_recording()
    
    # =========================================================================
    # RECORDING OPERATIONS
    # =========================================================================
    
    def _start_recording(self):
        """Start a new recording."""
        success, recording, error = self.recording_wrapper.start_recording()
        
        if not success:
            QMessageBox.critical(self, "Recording Error", 
                f"Cannot start recording:\n\n{error}")
            return
        
        logger.info("Recording started from UI")
    
    def _stop_recording(self):
        """
        Stop current recording.
        
        WORKFLOW:
        1. Stop recording
        2. Check if metadata exists
        3. If has metadata: Silent save
        4. If no metadata: Show dialog
        5. Reset UI
        """
        success, recording, error = self.recording_wrapper.stop_recording()
        
        if not success:
            QMessageBox.critical(self, "Stop Error", 
                f"Failed to stop:\n\n{error}")
            return
        
        # Handle metadata
        if self.metadata_handler.has_metadata():
            # Silent save
            success, error = self.metadata_handler.save_to_database(recording)
            if success:
                self.status_label.setText("✓ Recording Saved")
                QTimer.singleShot(TIMINGS['status_clear'], 
                    lambda: self.status_label.setText("Ready to Record"))
            else:
                QMessageBox.warning(self, "Save Warning",
                    f"Video saved but info not saved:\n{error}")
        elif not self.voice_mode_active:
            # Show dialog
            self.metadata_handler.show_metadata_dialog(recording)
        else:
            # Voice mode - silent save without info
            self.status_label.setText("✓ Recording Saved")
            QTimer.singleShot(TIMINGS['status_clear'],
                lambda: self.status_label.setText("Ready to Record"))
        
        # Reset
        self.metadata_handler.clear_metadata()
        self.voice_mode_active = False
        
        logger.info("Recording stopped from UI")
    
    # =========================================================================
    # STATE CHANGE HANDLERS
    # =========================================================================
    
    def _on_recording_state_change(self, state, recording):
        """
        Handle recording state changes.
        
        Called by RecordingControllerWrapper when state changes.
        
        Args:
            state: New RecordingState
            recording: Recording object
        """
        from app.utils.constants import RecordingState
        
        if state == RecordingState.RECORDING:
            # Update UI for recording
            self._update_ui_for_recording()
            
            # Start timers
            self.recording_timer.start()
            self.preview_update_timer.start(TIMINGS['timer_update'])
            self.dot_blink_timer.start(TIMINGS['dot_blink'])
            
        elif state == RecordingState.IDLE:
            # Update UI for idle
            self._update_ui_for_idle()
            
            # Stop timers
            self.recording_timer.stop()
            self.preview_update_timer.stop()
            self.dot_blink_timer.stop()
            
            # Clear preview
            self.preview_handler.clear_preview()
    
    def _on_recording_error(self, error_msg):
        """
        Handle recording errors from controller.
        
        Args:
            error_msg: Error message from RecordingController
        """
        QMessageBox.critical(self, "Recording Error",
            f"Recording stopped unexpectedly:\n\n{error_msg}")
        
        self._update_ui_for_idle()
        self.recording_timer.stop()
        self.preview_update_timer.stop()
        self.dot_blink_timer.stop()
        self.preview_handler.clear_preview()
    
    # =========================================================================
    # UI UPDATES
    # =========================================================================
    
    def _update_ui_for_recording(self):
        """Update UI when recording starts."""
        from .design_constants import get_record_button_style
        
        # Button
        self.record_btn.setText("STOP RECORDING")
        self.record_btn.setStyleSheet(get_record_button_style(is_recording=True))
        
        # Disable info button
        self.info_btn.setEnabled(False)
        
        # Status
        self.status_label.setText("Recording in Progress")
        self.status_label.setStyleSheet(f"color: {COLORS['danger']};")
        
        # Show recording indicator
        UIBuilder.update_recording_indicator(self.recording_indicator, visible=True)
    
    def _update_ui_for_idle(self):
        """Update UI when recording stops."""
        from .design_constants import get_record_button_style
        
        # Button
        self.record_btn.setText("START RECORDING")
        self.record_btn.setStyleSheet(get_record_button_style(is_recording=False))
        
        # Enable info button
        self.info_btn.setEnabled(True)
        
        # Status
        self.status_label.setText("Ready to Record")
        self.status_label.setStyleSheet(f"color: {COLORS['danger']};")
        
        # Hide recording indicator
        UIBuilder.update_recording_indicator(self.recording_indicator, visible=False)
    
    def _toggle_recording_indicator(self):
        """Toggle recording indicator dot (blink animation)."""
        self.dot_visible = not self.dot_visible
        UIBuilder.update_recording_indicator(self.recording_indicator, self.dot_visible)
    
    def _update_storage_display(self):
        """Update storage bar with real disk usage using shutil."""
        try:
            import shutil
            
            # Get disk usage for current drive directly
            total, used, free = shutil.disk_usage("/")
            percent_used = (used / total) * 100
            
            # Update progress bar value
            self.storage_bar.setValue(int(percent_used))
            
            # Format display based on free space
            free_gb = free / (1024 ** 3)  # Bytes to GB
            free_mb = free / (1024 ** 2)  # Bytes to MB
            
            if free_gb > 1:
                self.storage_bar.setFormat(
                    f"{percent_used:.1f}% used ({free_gb:.1f} GB free)"
                )
            else:
                self.storage_bar.setFormat(
                    f"{percent_used:.1f}% used ({free_mb:.0f} MB free)"
                )
            
            # Change color based on free space
            if free_mb < 100:
                # Critical - red
                self.storage_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {COLORS['background_dark']};
                        border-radius: 5px;
                        text-align: center;
                        height: 30px;
                    }}
                    QProgressBar::chunk {{ background-color: {COLORS['danger']}; }}
                """)
            elif free_mb < 500:
                # Low - orange
                self.storage_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {COLORS['background_dark']};
                        border-radius: 5px;
                        text-align: center;
                        height: 30px;
                    }}
                    QProgressBar::chunk {{ background-color: {COLORS['warning']}; }}
                """)
            else:
                # OK - green
                self.storage_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {COLORS['background_dark']};
                        border-radius: 5px;
                        text-align: center;
                        height: 30px;
                    }}
                    QProgressBar::chunk {{ background-color: {COLORS['success']}; }}
                """)
        
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            self.storage_bar.setFormat("Storage: unknown")
    
    # =========================================================================
    # VOICE COMMAND INTEGRATION
    # =========================================================================
    
    def voice_start_recording(self):
        """
        Start recording via voice command.
        
        Sets voice_mode_active flag for silent workflow.
        """
        self.voice_mode_active = True
        self._start_recording()
        logger.info("Recording started via voice command")
    
    def voice_stop_recording(self):
        """
        Stop recording via voice command.
        
        Uses silent save workflow (no dialog).
        """
        self._stop_recording()
        logger.info("Recording stopped via voice command")


__all__ = ['RecordingScreen']
