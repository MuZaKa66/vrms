"""
Recording Screen - LGH Branded Edition with Comprehensive Error Handling

Production-grade recording interface for Lahore General Hospital Eye Department.

Author: ZKB
Special Thanks: Dr. Farqaleet
Version: 2.1.0
Date: February 17, 2026
"""

import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPixmap

from app.utils.logger import AppLogger
from app.utils.constants import RecordingState
from app.gui.recording.design_constants import (
    SPACING, COLORS, SIZES, TIMINGS, LOGO_PATH,
    get_record_button_style, get_info_button_style,
    get_storage_bar_style, get_about_button_style
)
from app.gui.recording.ui_builder import UIBuilder
from app.gui.recording.preview_handler import PreviewHandler
from app.gui.recording.recording_controller_wrapper import (
    RecordingControllerWrapper, RecordingTimer
)
from app.gui.recording.metadata_handler import MetadataHandler

logger = AppLogger("RecordingScreen")


class RecordingScreen(QWidget):
    """Main recording interface - LGH Branded with robust error handling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dialog_open = False
        self._ui_locked = False
        self.preview_handler = None
        self.recording_wrapper = None
        self.recording_timer = None
        self.metadata_handler = None
        self.storage_check_timer = QTimer()
        self.dot_blink_timer = QTimer()
        self.preview_update_timer = QTimer()
        self.clock_update_timer = QTimer()
        self.dot_visible = True
        
        try:
            self._init_ui()
            self._setup_timers()
            self._update_storage_display()
            self._update_clock()
            logger.info("RecordingScreen initialized (LGH Edition)")
        except Exception as e:
            logger.error(f"Init failed: {e}")
            QMessageBox.critical(self, "Init Error", f"Failed to initialize:\n{e}")
    
    def _init_ui(self):
        """Build UI with LGH branding."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status bar
        self._create_status_bar(main_layout)
        
        # Content area
        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['background']};")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(SPACING['sm'])
        content_layout.setContentsMargins(
            SPACING['md'], SPACING['md'], SPACING['md'], SPACING['xxl']
        )
        
        # Status label
        self.status_label = UIBuilder.create_status_label()
        content_layout.addWidget(self.status_label)
        
        # Info row
        self._create_info_row(content_layout)
        
        # Timer
        content_layout.addSpacing(SPACING['xs'])
        self.timer_label = UIBuilder.create_timer_label()
        content_layout.addWidget(self.timer_label)
        
        # Controls (button + preview)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(SPACING['md'])
        
        # Button
        button_container = QVBoxLayout()
        button_container.addStretch()
        self.record_btn = UIBuilder.create_record_button(is_recording=False)
        self.record_btn.clicked.connect(self._on_record_button_clicked)
        button_container.addWidget(self.record_btn, alignment=Qt.AlignCenter)
        button_container.addStretch()
        controls_layout.addLayout(button_container, 3)
        
        # Preview
        (preview_container, self.preview_label,
         self.recording_indicator, preview_buffer) = UIBuilder.create_preview_container()
        controls_layout.addWidget(preview_container, 0, Qt.AlignRight | Qt.AlignVCenter)
        
        content_layout.addLayout(controls_layout)
        
        # About button
        about_layout = QHBoxLayout()
        about_layout.addStretch()
        self.about_btn = QPushButton("ℹ")
        self.about_btn.setFixedSize(SIZES['about_button'][0], SIZES['about_button'][1])
        self.about_btn.setStyleSheet(get_about_button_style())
        self.about_btn.clicked.connect(self._show_about_dialog)
        about_layout.addWidget(self.about_btn)
        content_layout.addLayout(about_layout)
        
        main_layout.addWidget(content)
        
        # Initialize components
        self.preview_handler = PreviewHandler(
            self.preview_label, preview_buffer, None, throttle=TIMINGS['preview_throttle']
        )
        self.recording_wrapper = RecordingControllerWrapper(
            on_state_change=self._on_recording_state_change,
            on_error=self._on_recording_error
        )
        self.preview_handler.controller = self.recording_wrapper.controller
        self.recording_timer = RecordingTimer(self.timer_label, self.recording_wrapper)
        self.metadata_handler = MetadataHandler(
            self.info_display, self.info_btn, self.clear_btn, self
        )
    
    def _create_status_bar(self, parent_layout):
        """Create top status bar with logo, storage, clock."""
        status_bar = QFrame()
        status_bar.setFixedHeight(SIZES['status_bar_height'])
        status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['status_bar_bg']};
                border-bottom: 2px solid {COLORS['success']};
            }}
        """)
        
        bar_layout = QHBoxLayout(status_bar)
        bar_layout.setContentsMargins(10, 0, 10, 0)
        bar_layout.setSpacing(15)
        
        # Logo
        logo_label = QLabel()
        try:
            import os
            if os.path.exists(LOGO_PATH):
                pixmap = QPixmap(LOGO_PATH)
                pixmap = pixmap.scaled(
                    SIZES['logo_size'][0], SIZES['logo_size'][1],
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                logo_label.setPixmap(pixmap)
            else:
                logo_label.setText("🏥")
                logo_label.setFont(QFont("Arial", 14))
                logo_label.setStyleSheet(f"color: {COLORS['status_bar_text']};")
        except Exception as e:
            logo_label.setText("🏥")
            logo_label.setFont(QFont("Arial", 14))
            logo_label.setStyleSheet(f"color: {COLORS['status_bar_text']};")
            logger.error(f"Logo load failed: {e}")
        
        bar_layout.addWidget(logo_label)
        
        # Status dot + text
        self.status_dot = QLabel("●")
        self.status_dot.setFont(QFont("Arial", 12))
        self.status_dot.setStyleSheet(f"color: {COLORS['status_ready']};")
        bar_layout.addWidget(self.status_dot)
        
        self.status_text = QLabel("Ready")
        self.status_text.setFont(QFont("Arial", SIZES['font_status'], QFont.Bold))
        self.status_text.setStyleSheet(f"color: {COLORS['status_bar_text']};")
        bar_layout.addWidget(self.status_text)
        
        # Storage
        storage_container = QWidget()
        storage_layout = QHBoxLayout(storage_container)
        storage_layout.setContentsMargins(0, 0, 0, 0)
        storage_layout.setSpacing(8)
        
        storage_label = QLabel("Storage:")
        storage_label.setFont(QFont("Arial", SIZES['font_storage'], QFont.Bold))
        storage_label.setStyleSheet(f"color: {COLORS['status_bar_text']};")
        storage_layout.addWidget(storage_label)
        
        self.storage_bar = QProgressBar()
        self.storage_bar.setMinimum(0)
        self.storage_bar.setMaximum(100)
        self.storage_bar.setValue(0)
        self.storage_bar.setFixedWidth(200)
        self.storage_bar.setStyleSheet(get_storage_bar_style('ok'))
        storage_layout.addWidget(self.storage_bar)
        
        bar_layout.addWidget(storage_container)
        bar_layout.addStretch()
        
        # Clock
        self.clock_label = QLabel()
        self.clock_label.setFont(QFont("Arial", SIZES['font_clock'], QFont.Bold))
        self.clock_label.setStyleSheet(f"color: {COLORS['status_bar_text']};")
        bar_layout.addWidget(self.clock_label)
        
        parent_layout.addWidget(status_bar)
    
    def _create_info_row(self, parent_layout):
        """Create info button + display row."""
        info_layout = QHBoxLayout()
        info_layout.setSpacing(SPACING['md'])
        
        self.info_btn = UIBuilder.create_info_button(has_info=False)
        self.info_btn.clicked.connect(self._on_info_button_clicked)
        info_layout.addWidget(self.info_btn)
        
        self.clear_btn = UIBuilder.create_clear_button()
        self.clear_btn.clicked.connect(self._on_clear_button_clicked)
        info_layout.addWidget(self.clear_btn)
        
        self.info_display = UIBuilder.create_info_display_label()
        info_layout.addWidget(self.info_display, 1)
        
        parent_layout.addLayout(info_layout)
    
    def _setup_timers(self):
        """Setup periodic timers."""
        self.storage_check_timer.timeout.connect(self._safe_update_storage)
        self.storage_check_timer.start(TIMINGS['storage_check'])
        
        self.preview_update_timer.timeout.connect(self._safe_update_preview)
        self.dot_blink_timer.timeout.connect(self._toggle_recording_indicator)
        
        self.clock_update_timer.timeout.connect(self._safe_update_clock)
        self.clock_update_timer.start(TIMINGS['clock_update'])
    
    def _on_info_button_clicked(self):
        """Handle info button click."""
        try:
            self._dialog_open = True
            result = self.metadata_handler.show_metadata_dialog(recording=None)
            if result:
                self.status_label.setText("✓ Info Added - Ready")
                self.status_label.setStyleSheet(f"color: {COLORS['success']};")
                QTimer.singleShot(TIMINGS['status_clear'], self._reset_status)
        except Exception as e:
            logger.error(f"Info dialog error: {e}")
        finally:
            self._dialog_open = False
    
    def _on_clear_button_clicked(self):
        """Handle clear button."""
        try:
            self.metadata_handler.confirm_clear()
        except Exception as e:
            logger.error(f"Clear error: {e}")
    
    def _on_record_button_clicked(self):
        """Handle record button click."""
        if self._ui_locked:
            return
        
        try:
            if self.recording_wrapper.state == RecordingState.IDLE:
                self._start_recording()
            elif self.recording_wrapper.state == RecordingState.RECORDING:
                self._stop_recording()
        except Exception as e:
            logger.error(f"Button click error: {e}")
            self._handle_recording_error(str(e))
    
    def _start_recording(self):
        """Start recording with pre-flight checks."""
        self._ui_locked = True
        
        try:
            if not self._check_storage_available():
                self._ui_locked = False
                return
            
            success, recording, error = self.recording_wrapper.start_recording()
            
            if not success:
                QMessageBox.critical(
                    self, "Recording Failed",
                    f"Cannot start:\n\n{error}\n\nCheck camera connection."
                )
                self._ui_locked = False
                return
            
            logger.info("Recording started")
        except Exception as e:
            logger.error(f"Start error: {e}")
            self._handle_recording_error(str(e))
        finally:
            self._ui_locked = False
    
    def _stop_recording(self):
        """Stop recording gracefully."""
        self._ui_locked = True
        self.record_btn.setEnabled(False)
        self.status_label.setText("Stopping...")
        
        try:
            success, recording, error = self.recording_wrapper.stop_recording()
            
            if not success:
                QMessageBox.critical(self, "Stop Error", f"Failed:\n\n{error}")
                self._ui_locked = False
                self.record_btn.setEnabled(True)
                return
            
            self._handle_metadata_after_recording(recording)
            self.metadata_handler.clear_metadata()
            logger.info("Recording stopped")
            
        except Exception as e:
            logger.error(f"Stop error: {e}")
            self._handle_recording_error(str(e))
        finally:
            self._ui_locked = False
            self.record_btn.setEnabled(True)
    
    def _handle_metadata_after_recording(self, recording):
        """Handle metadata after recording."""
        try:
            if self.metadata_handler.has_metadata():
                success, error = self.metadata_handler.save_to_database(recording)
                if success:
                    self.status_label.setText("✓ Saved")
                    self.status_label.setStyleSheet(f"color: {COLORS['success']};")
                    QTimer.singleShot(TIMINGS['status_clear'], self._reset_status)
                else:
                    QMessageBox.warning(self, "Save Warning", f"Info not saved:\n{error}")
            else:
                self._dialog_open = True
                self.metadata_handler.show_metadata_dialog(recording)
                self._dialog_open = False
        except Exception as e:
            logger.error(f"Metadata error: {e}")
    
    def _check_storage_available(self):
        """Check storage before recording."""
        try:
            total, used, free = shutil.disk_usage("/")
            free_mb = free / (1024 ** 2)
            
            if free_mb < 100:
                QMessageBox.critical(
                    self, "Critical Storage",
                    f"Only {free_mb:.0f} MB free.\nCannot record."
                )
                return False
            elif free_mb < 500:
                reply = QMessageBox.warning(
                    self, "Low Storage",
                    f"Only {free_mb:.0f} MB free.\nContinue?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                return reply == QMessageBox.Yes
            return True
        except Exception as e:
            logger.error(f"Storage check failed: {e}")
            return True
    
    def _on_recording_state_change(self, state, recording):
        """Handle state changes."""
        try:
            if state == RecordingState.RECORDING:
                self._update_ui_for_recording()
                self.recording_timer.start()
                self.preview_update_timer.start(TIMINGS['timer_update'])
                self.dot_blink_timer.start(TIMINGS['dot_blink'])
            elif state == RecordingState.IDLE:
                self._update_ui_for_idle()
                self.recording_timer.stop()
                self.preview_update_timer.stop()
                self.dot_blink_timer.stop()
                self.preview_handler.clear_preview()
        except Exception as e:
            logger.error(f"State change error: {e}")
            self._recover_from_error()
    
    def _on_recording_error(self, error_msg):
        """Handle recording thread errors."""
        QMessageBox.critical(
            self, "Recording Error",
            f"Stopped unexpectedly:\n\n{error_msg}\n\nVideo saved if possible."
        )
        self._recover_from_error()
    
    def _update_ui_for_recording(self):
        """Update UI for recording state."""
        self.record_btn.setText("STOP RECORDING")
        self.record_btn.setStyleSheet(get_record_button_style(is_recording=True))
        self.info_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.status_label.setText("Recording")
        self.status_label.setStyleSheet(f"color: {COLORS['danger']};")
        self.status_dot.setStyleSheet(f"color: {COLORS['status_recording']};")
        self.status_text.setText("Recording")
        UIBuilder.update_recording_indicator(self.recording_indicator, visible=True)
    
    def _update_ui_for_idle(self):
        """Update UI for idle state."""
        self.record_btn.setText("START RECORDING")
        self.record_btn.setStyleSheet(get_record_button_style(is_recording=False))
        self.info_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self._reset_status()
        self.status_dot.setStyleSheet(f"color: {COLORS['status_ready']};")
        self.status_text.setText("Ready")
        UIBuilder.update_recording_indicator(self.recording_indicator, visible=False)
    
    def _reset_status(self):
        """Reset status label."""
        self.status_label.setText("Ready to Record")
        self.status_label.setStyleSheet(f"color: {COLORS['danger']};")
    
    def _toggle_recording_indicator(self):
        """Toggle recording dot."""
        self.dot_visible = not self.dot_visible
        UIBuilder.update_recording_indicator(self.recording_indicator, self.dot_visible)
    
    def _safe_update_storage(self):
        """Safe storage update."""
        try:
            self._update_storage_display()
        except Exception as e:
            logger.error(f"Storage update failed: {e}")
    
    def _safe_update_preview(self):
        """Safe preview update."""
        try:
            self.preview_handler.update_preview()
        except Exception as e:
            logger.error(f"Preview update failed: {e}")
    
    def _safe_update_clock(self):
        """Safe clock update."""
        try:
            self._update_clock()
        except Exception as e:
            logger.error(f"Clock update failed: {e}")
    
    def _update_storage_display(self):
        """Update storage bar."""
        try:
            total, used, free = shutil.disk_usage("/")
            percent_used = (used / total) * 100
            self.storage_bar.setValue(int(percent_used))
            
            free_gb = free / (1024 ** 3)
            free_mb = free / (1024 ** 2)
            
            if free_gb > 1:
                self.storage_bar.setFormat(f"{percent_used:.1f}% ({free_gb:.1f} GB free)")
            else:
                self.storage_bar.setFormat(f"{percent_used:.1f}% ({free_mb:.0f} MB free)")
            
            if free_mb < 100:
                self.storage_bar.setStyleSheet(get_storage_bar_style('critical'))
            elif free_mb < 500:
                self.storage_bar.setStyleSheet(get_storage_bar_style('low'))
            else:
                self.storage_bar.setStyleSheet(get_storage_bar_style('ok'))
        except Exception as e:
            logger.error(f"Storage display failed: {e}")
            self.storage_bar.setFormat("unknown")
    
    def _update_clock(self):
        """Update live clock."""
        try:
            now = datetime.now()
            self.clock_label.setText(now.strftime("%a  %d %b  %H:%M"))
        except Exception as e:
            logger.error(f"Clock update failed: {e}")
            self.clock_label.setText("--:--")
    
    def _show_about_dialog(self):
        """Show about dialog."""
        try:
            from app.gui.dialogs.about_dialog import AboutDialog
            dialog = AboutDialog(self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"About dialog error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to show about:\n{e}")
    
    def _handle_recording_error(self, error_msg):
        """Handle recording errors."""
        logger.error(f"Recording error: {error_msg}")
        QMessageBox.critical(
            self, "Error",
            f"Error:\n\n{error_msg}\n\nAttempting recovery."
        )
        self._recover_from_error()
    
    def _recover_from_error(self):
        """Recover from error state."""
        try:
            logger.info("Recovering from error...")
            self.recording_timer.stop()
            self.preview_update_timer.stop()
            self.dot_blink_timer.stop()
            try:
                self.preview_handler.clear_preview()
            except:
                pass
            self._update_ui_for_idle()
            self._ui_locked = False
            self._dialog_open = False
            logger.info("Recovery complete")
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
    
    def is_recording(self):
        """Check if recording (for main_window.py)."""
        try:
            return self.recording_wrapper.state == RecordingState.RECORDING
        except:
            return False
    
    def is_dialog_open(self):
        """Check if dialog open (for main_window.py)."""
        return self._dialog_open
    
    def voice_start_recording(self):
        """Voice command start."""
        try:
            self._start_recording()
            logger.info("Voice start")
        except Exception as e:
            logger.error(f"Voice start failed: {e}")
    
    def voice_stop_recording(self):
        """Voice command stop."""
        try:
            self._stop_recording()
            logger.info("Voice stop")
        except Exception as e:
            logger.error(f"Voice stop failed: {e}")


__all__ = ['RecordingScreen']
