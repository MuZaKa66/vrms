"""
File: app/gui/recording/recording_screen.py

Recording Screen - Video Recording Management System
Lahore General Hospital, Eye Department

TWO-COLUMN LAYOUT within content area (1024 x 440px):

  IDLE STATE:
  ┌──────────────────────────────────────────────────────────────┐
  │ [Add Info]  [Clear]   Patient: John Doe                      │ 65px info row
  ├───────────────────────────┬──────────────────────────────────┤
  │                           │  Ready to Record                 │ status label
  │                           │ ┌──────────────────────────────┐ │
  │    START                  │ │                              │ │
  │  RECORDING                │ │    LIVE  PREVIEW             │ │
  │  (green btn)              │ │                              │ │
  │                           │ └──────────────────────────────┘ │
  └───────────────────────────┴──────────────────────────────────┘

  RECORDING STATE:
  ┌──────────────────────────────────────────────────────────────┐
  │  (info row hidden)                                           │
  ├───────────────────────────┬──────────────────────────────────┤
  │  00:14:32  (timer)        │  ● RECORDING  (blinks)           │
  │                           │ ┌──────────────────────────────┐ │
  │    STOP                   │ │                              │ │
  │  RECORDING                │ │    LIVE  PREVIEW             │ │
  │  (red btn)                │ │                              │ │
  │                           │ └──────────────────────────────┘ │
  └───────────────────────────┴──────────────────────────────────┘

KEY DESIGN DECISIONS:
  - No internal status bar (top bar consolidated in main_window)
  - info_row_widget hides/shows as a single unit on state change
  - timer_label (above record btn): hidden idle, shown recording
  - status_label (above preview):   always visible, text changes
  - recording_indicator replaced by status_label blink
  - setFixedSize ONLY on buttons/preview (no min/max — causes collapse)

Author: ZKB
Special Thanks: Dr. Farqaleet
Hospital: Lahore General Hospital - Eye Department
Date: April 9, 2026
Version: 3.2.0

Changelog:
  v3.2.0 - Robustness pass:
           - _on_recording_error / _handle_recording_error consolidated
           - _on_record_button_clicked handles ERROR state (button no longer dead)
           - _recover_from_error calls controller.force_stop() to reset state
           - _dialog_open flag protected by try/finally in Path B
           - MIN_RECORDING_DURATION_SECONDS enforced before stop
           - "Ready to Record" status uses success colour (not danger/red)
           - Duplicate storage check removed (controller handles it)
  v3.1.0 - Two-column layout, status_label blink, info row improvements
  v3.0.0 - Internal status bar removed, post-recording dialog restored
  v2.1.0 - LGH branded edition
"""

import shutil
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox,
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

from app.utils.logger import AppLogger
from app.utils.constants import RecordingState
from app.gui.recording.design_constants import (
    SPACING, COLORS, SIZES, TIMINGS,
    get_record_button_style,
    get_info_button_style,
)
from app.gui.recording.ui_builder import UIBuilder
from app.gui.recording.preview_handler import PreviewHandler
from app.gui.recording.recording_controller_wrapper import (
    RecordingControllerWrapper, RecordingTimer,
)
from app.gui.recording.metadata_handler import MetadataHandler
from config.app_config import MIN_RECORDING_DURATION_SECONDS

logger = AppLogger("RecordingScreen")


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS: RecordingScreen
# ═══════════════════════════════════════════════════════════════════════════════

class RecordingScreen(QWidget):
    """
    Primary recording interface — two-column layout.

    LEFT COLUMN:
        timer_label  (hidden in idle, shown during recording)
        record_btn   (START green / STOP red)

    RIGHT COLUMN:
        status_label ("Ready to Record" idle / "● RECORDING" blinks)
        preview_container (bezel-styled video panel)

    TOP (always visible when idle, hidden during recording):
        info_row_widget — Add Info | Clear | patient info display

    Attributes:
        info_row_widget     (QWidget)       — hides during recording
        info_btn            (QPushButton)   — Add / Edit Info
        clear_btn           (QPushButton)   — Clear metadata
        info_display        (QLabel)        — patient/procedure text

        status_label        (QLabel)        — in info_row (right side), idle only
        recording_indicator (QLabel)        — above preview, recording only
        timer_label         (QLabel)        — above record btn, recording only
        record_btn          (QPushButton)
        preview_label       (QLabel)

        preview_handler     (PreviewHandler)
        recording_wrapper   (RecordingControllerWrapper)
        recording_timer     (RecordingTimer)
        metadata_handler    (MetadataHandler)

        dot_blink_timer     (QTimer)        — active during recording
        preview_update_timer(QTimer)        — active during recording

        _dialog_open (bool)  — True while any dialog is open
        _ui_locked   (bool)  — True during start/stop transition
        _dot_visible (bool)  — current blink state
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._dialog_open = False
        self._ui_locked   = False
        self._dot_visible = True

        self.preview_handler    = None
        self.recording_wrapper  = None
        self.recording_timer    = None
        self.metadata_handler   = None

        self.dot_blink_timer      = QTimer()
        self.preview_update_timer = QTimer()

        try:
            self._init_ui()
            self._setup_timers()
            logger.info("RecordingScreen initialised (v3.2.0)")
        except Exception as e:
            logger.error(f"RecordingScreen init failed: {e}")
            QMessageBox.critical(self, "Init Error", f"Failed to initialise:\n{e}")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: UI INITIALISATION
    # ─────────────────────────────────────────────────────────────────────────

    def _init_ui(self):
        """
        Build the recording screen layout.

        Structure:
          QVBoxLayout (main)
            └── content QWidget
                  └── QVBoxLayout
                        ├── info_row_widget   [hidden during recording]
                        └── controls QHBoxLayout
                              ├── left_col QVBoxLayout
                              │     ├── timer_label   [hidden idle]
                              │     └── record_btn
                              └── right_col QVBoxLayout
                                    ├── status_label  [always shown]
                                    └── preview_container
        """
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['background']};")

        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(SPACING['sm'])
        content_layout.setContentsMargins(
            SPACING['md'], SPACING['md'],
            SPACING['md'], SPACING['sm'],
        )

        # Info row (Add Info + patient info display)
        self._build_info_row(content_layout)

        # Two-column controls (timer+button | status+preview)
        self._build_controls(content_layout)

        main_layout.addWidget(content)

        # ── Initialise service components ─────────────────────────────────────
        self.preview_handler = PreviewHandler(
            self.preview_label,
            self._preview_buffer,
            None,
            throttle=TIMINGS['preview_throttle'],
        )
        self.recording_wrapper = RecordingControllerWrapper(
            on_state_change=self._on_recording_state_change,
            on_error=self._on_recording_error,
        )
        self.preview_handler.controller = self.recording_wrapper.controller

        self.recording_timer = RecordingTimer(
            self.timer_label, self.recording_wrapper
        )
        self.metadata_handler = MetadataHandler(
            self.info_display,
            self.info_btn,
            self.clear_btn,
            self,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: INFO ROW  (top of content, hidden during recording)
    # ─────────────────────────────────────────────────────────────────────────

    def _build_info_row(self, parent_layout):
        """
        Build the info row and add it to parent_layout.

        Row layout (left → right):
          [Add Info btn]  [Clear btn (hidden)]  [patient info text]

        The entire info_row_widget hides when recording starts
        and reappears when recording stops.
        """
        self.info_row_widget = QWidget()
        self.info_row_widget.setStyleSheet("background: transparent;")
        self.info_row_widget.setFixedHeight(SIZES['info_row_height'])

        row = QHBoxLayout(self.info_row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACING['md'])

        self.info_btn = UIBuilder.create_info_button(has_info=False)
        self.info_btn.clicked.connect(self._on_info_button_clicked)
        row.addWidget(self.info_btn)

        self.clear_btn = UIBuilder.create_clear_button()
        self.clear_btn.clicked.connect(self._on_clear_button_clicked)
        row.addWidget(self.clear_btn)

        self.info_display = UIBuilder.create_info_display_label()
        row.addWidget(self.info_display, stretch=1)

        self.status_label = UIBuilder.create_status_label()
        row.addWidget(self.status_label, stretch=1)

        parent_layout.addWidget(self.info_row_widget)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: CONTROLS  (two-column: left=timer+btn, right=status+preview)
    # ─────────────────────────────────────────────────────────────────────────

    def _build_controls(self, parent_layout):
        """
        Build the two-column controls area and add to parent_layout.
        """
        controls = QHBoxLayout()
        controls.setSpacing(SPACING['md'])
        controls.setContentsMargins(0, 0, 0, 0)

        # ── LEFT COLUMN ───────────────────────────────────────────────────────
        left_col = QVBoxLayout()
        left_col.setSpacing(SPACING['xs'])
        left_col.setContentsMargins(0, 0, 0, 0)

        self.timer_label = UIBuilder.create_timer_label()
        self.timer_label.setFixedHeight(SIZES['info_row_height'])
        left_col.addWidget(self.timer_label, 0, Qt.AlignLeft)
        left_col.addStretch()

        self.record_btn = UIBuilder.create_record_button(is_recording=False)
        self.record_btn.clicked.connect(self._on_record_button_clicked)
        left_col.addWidget(self.record_btn, 0, Qt.AlignLeft)

        left_col.addStretch()
        controls.addLayout(left_col, stretch=1)

        # ── RIGHT COLUMN ──────────────────────────────────────────────────────
        right_col = QVBoxLayout()
        right_col.setSpacing(SPACING['xs'])
        right_col.setContentsMargins(0, 0, 0, 0)

        self.recording_indicator = QLabel("")
        self.recording_indicator.setFont(
            QFont("Arial", SIZES['font_status'], QFont.Bold)
        )
        self.recording_indicator.setFixedHeight(SIZES['info_row_height'])
        self.recording_indicator.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.recording_indicator.setStyleSheet(
            f"color: {COLORS['danger']}; background: transparent;"
        )
        self.recording_indicator.setVisible(False)
        right_col.addWidget(self.recording_indicator, 0, Qt.AlignLeft)

        (
            preview_container,
            self.preview_label,
            self._preview_buffer,
        ) = UIBuilder.create_preview_container()

        right_col.addWidget(preview_container, 0, Qt.AlignTop)

        controls.addLayout(right_col, 0)

        parent_layout.addLayout(controls)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: TIMER SETUP
    # ─────────────────────────────────────────────────────────────────────────

    def _setup_timers(self):
        """Connect recording-active timers to their slots."""
        self.preview_update_timer.timeout.connect(self._safe_update_preview)
        self.dot_blink_timer.timeout.connect(self._toggle_recording_indicator)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: BUTTON CLICK HANDLERS
    # ─────────────────────────────────────────────────────────────────────────

    def _on_info_button_clicked(self):
        """Handle Add Info / Edit Info tap."""
        try:
            self._dialog_open = True
            result = self.metadata_handler.show_metadata_dialog(recording=None)
            if result:
                self.status_label.setText("  Info Added - Ready")
                self.status_label.setStyleSheet(
                    f"color: {COLORS['success']}; "
                    f"font-weight: bold; background: transparent;"
                )
                QTimer.singleShot(TIMINGS['status_clear'], self._reset_status)
        except Exception as e:
            logger.error(f"Info dialog error: {e}")
        finally:
            self._dialog_open = False

    def _on_clear_button_clicked(self):
        """Handle Clear tap."""
        try:
            self.metadata_handler.confirm_clear()
        except Exception as e:
            logger.error(f"Clear error: {e}")

    def _on_record_button_clicked(self):
        """
        Handle START / STOP tap.

        State routing:
          IDLE      → _start_recording()
          RECORDING → _stop_recording()
          ERROR     → _recover_from_error()  (button no longer dead after error)
          Other     → ignored (transitional state)
        """
        if self._ui_locked:
            return
        try:
            state = self.recording_wrapper.state
            if state == RecordingState.IDLE:
                self._start_recording()
            elif state == RecordingState.RECORDING:
                self._stop_recording()
            elif state in (RecordingState.ERROR, RecordingState.STOPPING):
                # Controller is stuck — force reset and return to idle
                self._recover_from_error()
        except Exception as e:
            logger.error(f"Record button error: {e}")
            self._on_recording_error(str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING CONTROL
    # ─────────────────────────────────────────────────────────────────────────

    def _start_recording(self):
        """Start recording. Storage check done at UI level for UX feedback."""
        self._ui_locked = True
        try:
            if not self._check_storage_available():
                return
            success, recording, error = self.recording_wrapper.start_recording()
            if not success:
                QMessageBox.critical(
                    self, "Recording Failed",
                    f"Cannot start:\n\n{error}\n\nCheck camera connection."
                )
                return
            logger.info("Recording started")
        except Exception as e:
            logger.error(f"Start recording error: {e}")
            self._on_recording_error(str(e))
        finally:
            self._ui_locked = False

    def _stop_recording(self):
        """
        Stop recording and handle post-recording metadata.

        Enforces MIN_RECORDING_DURATION_SECONDS — asks user to confirm
        if recording is shorter than the minimum.
        """
        # ── Minimum duration check ─────────────────────────────────────────
        elapsed = self.recording_wrapper.get_elapsed_time()
        if elapsed < MIN_RECORDING_DURATION_SECONDS:
            reply = QMessageBox.question(
                self, "Short Recording",
                f"Recording is only {elapsed}s long "
                f"(minimum {MIN_RECORDING_DURATION_SECONDS}s).\n\n"
                "Stop anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self._ui_locked = True
        self.record_btn.setEnabled(False)
        self.status_label.setText("Stopping...")

        try:
            success, recording, error = self.recording_wrapper.stop_recording()
            if not success:
                QMessageBox.critical(
                    self, "Stop Error", f"Failed to stop:\n\n{error}"
                )
                return
            # clear_metadata only on confirmed success
            self._handle_metadata_after_recording(recording)
            self.metadata_handler.clear_metadata()
            logger.info("Recording stopped")
        except Exception as e:
            logger.error(f"Stop recording error: {e}")
            self._on_recording_error(str(e))
        finally:
            self._ui_locked = False
            self.record_btn.setEnabled(True)

    def _check_storage_available(self):
        """
        Verify sufficient SSD free space before starting a recording.

        < 100 MB: Critical — block recording
        < 500 MB: Low      — warn + ask to continue

        Note: Controller also checks storage internally. This UI-level check
        gives friendly feedback before the controller call is made.

        Returns:
            bool: True if recording may proceed
        """
        try:
            from config.app_config import VIDEO_STORAGE_PATH
            total, used, free = shutil.disk_usage(VIDEO_STORAGE_PATH)
            free_mb = free / (1024 ** 2)
            if free_mb < 100:
                QMessageBox.critical(
                    self, "Critical Storage",
                    f"Only {free_mb:.0f} MB free on storage SSD.\n"
                    "Cannot start recording."
                )
                return False
            elif free_mb < 500:
                reply = QMessageBox.warning(
                    self, "Low Storage",
                    f"Only {free_mb:.0f} MB free on storage SSD.\n"
                    "Continue recording?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
                )
                return reply == QMessageBox.Yes
            return True
        except Exception as e:
            logger.error(f"Storage check failed: {e}")
            return True   # fail open — do not block on check error

    def _handle_metadata_after_recording(self, recording):
        """
        Handle metadata after recording stops.

        PATH A — pre-added info (has_metadata() True):
            Silent database save. Shows "Saved" confirmation.

        PATH B — no pre-added info (has_metadata() False):
            Show post-recording metadata dialog with the recording object.
            User may fill and save, OR cancel — video is saved either way.
        """
        try:
            if self.metadata_handler.has_metadata():
                # Path A: silently save pre-added info
                success, error = self.metadata_handler.save_to_database(recording)
                if success:
                    self.status_label.setText("  Saved")
                    self.status_label.setStyleSheet(
                        f"color: {COLORS['success']}; "
                        f"font-weight: bold; background: transparent;"
                    )
                    QTimer.singleShot(TIMINGS['status_clear'], self._reset_status)
                else:
                    QMessageBox.warning(
                        self, "Save Warning",
                        f"Recording saved but info not written:\n{error}"
                    )
            else:
                # Path B: post-recording dialog — _dialog_open protected by try/finally
                try:
                    self._dialog_open = True
                    self.metadata_handler.show_metadata_dialog(recording)
                finally:
                    self._dialog_open = False

        except Exception as e:
            logger.error(f"Metadata post-save error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: STATE CHANGE HANDLERS
    # ─────────────────────────────────────────────────────────────────────────

    def _on_recording_state_change(self, state, recording):
        """
        React to state transitions from RecordingControllerWrapper.

        RECORDING → _update_ui_for_recording() + start timers
        IDLE      → _update_ui_for_idle()       + stop timers
        """
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
        """
        Primary error handler — called from:
          - recording thread (via wrapper's QTimer.singleShot marshal)
          - button handlers on exception
          - state change handler on exception

        Always safe to call Qt widgets here — either already on main thread
        or marshalled by wrapper before reaching this method.
        """
        logger.error(f"Recording error: {error_msg}")
        QMessageBox.critical(
            self, "Recording Error",
            f"Recording stopped unexpectedly:\n\n{error_msg}\n\n"
            "Video has been saved if possible."
        )
        self._recover_from_error()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: UI STATE UPDATES  (IDLE <-> RECORDING)
    # ─────────────────────────────────────────────────────────────────────────

    def _update_ui_for_recording(self):
        """Switch content area to RECORDING state."""
        self.info_row_widget.setVisible(False)
        self.timer_label.setVisible(True)

        self.recording_indicator.setVisible(True)
        self.recording_indicator.setText("● RECORDING")

        self.record_btn.setText("STOP\nRECORDING")
        self.record_btn.setStyleSheet(get_record_button_style(is_recording=True))
        logger.debug("UI -> RECORDING")

    def _update_ui_for_idle(self):
        """Switch content area back to IDLE state."""
        self.timer_label.setVisible(False)
        self.info_row_widget.setVisible(True)

        self.recording_indicator.setVisible(False)
        self.recording_indicator.setText("")

        self.record_btn.setText("START\nRECORDING")
        self.record_btn.setStyleSheet(get_record_button_style(is_recording=False))

        self.info_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)

        self._reset_status()
        logger.debug("UI -> IDLE")

    def _reset_status(self):
        """Reset status_label to default 'Ready to Record'."""
        self.status_label.setText("Ready to Record")
        self.status_label.setStyleSheet(
            # success colour (green) — not danger/red which reads as an error
            f"color: {COLORS['success']}; background: transparent;"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: PERIODIC SLOT METHODS
    # ─────────────────────────────────────────────────────────────────────────

    def _safe_update_preview(self):
        """Update video preview frame (errors logged, recording unaffected)."""
        try:
            self.preview_handler.update_preview()
        except Exception as e:
            logger.error(f"Preview update error: {e}")

    def _toggle_recording_indicator(self):
        """Blink the '● RECORDING' label above the preview."""
        self._dot_visible = not self._dot_visible
        UIBuilder.update_recording_indicator(
            self.recording_indicator, self._dot_visible
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: ERROR RECOVERY
    # ─────────────────────────────────────────────────────────────────────────

    def _recover_from_error(self):
        """
        Return UI and controller to clean idle state after any error.

        Steps:
        1. Stop all timers
        2. Clear preview
        3. Call controller.force_stop() — resets controller to IDLE
           regardless of its current state (RECORDING, ERROR, STOPPING, etc.)
        4. Reset UI to idle appearance
        5. Release all locks and flags
        """
        try:
            logger.info("Recovering from error...")

            # Stop all timers
            self.recording_timer.stop()
            self.preview_update_timer.stop()
            self.dot_blink_timer.stop()

            # Clear preview
            try:
                self.preview_handler.clear_preview()
            except Exception:
                pass

            # Force-reset controller — without this, controller stays in ERROR
            # and the next start_recording() call will fail silently
            try:
                self.recording_wrapper.controller.force_stop()
            except Exception as e:
                logger.error(f"force_stop failed during recovery: {e}")

            # Reset UI
            self._update_ui_for_idle()
            self._ui_locked   = False
            self._dialog_open = False

            logger.info("Recovery complete")

        except Exception as e:
            logger.error(f"Recovery failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: PUBLIC API  (called by main_window and voice handler)
    # ─────────────────────────────────────────────────────────────────────────

    def is_recording(self):
        """Check whether recording is currently active."""
        try:
            return self.recording_wrapper.state == RecordingState.RECORDING
        except Exception:
            return False

    def is_dialog_open(self):
        """Check whether a modal dialog is open."""
        return self._dialog_open

    def voice_start_recording(self):
        """Start recording via voice command."""
        try:
            self._start_recording()
        except Exception as e:
            logger.error(f"Voice start error: {e}")

    def voice_stop_recording(self):
        """Stop recording via voice command."""
        try:
            self._stop_recording()
        except Exception as e:
            logger.error(f"Voice stop error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = ['RecordingScreen']
