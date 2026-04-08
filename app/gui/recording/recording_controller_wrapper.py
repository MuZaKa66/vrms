"""
File: app/gui/recording/recording_controller_wrapper.py

Recording Controller Wrapper - State Management

Wraps the RecordingController to provide high-level recording operations.
Handles state transitions, error handling, and UI updates.

CRITICAL THREAD SAFETY:
    _handle_controller_error() receives callbacks FROM the recording thread.
    It must NEVER call Qt widget methods directly.
    QTimer.singleShot(0, ...) marshals the call to the main thread safely.

Author: OT Video Dev Team
Date: April 9, 2026
Version: 2.1.0
Changelog:
    - v2.1.0: Fixed thread violation — error callback now marshalled to main
              thread via QTimer.singleShot(0, ...) before touching any Qt UI.
              Added is_recording(), is_idle(), is_error() convenience methods.
    - v2.0.0: Refactored
"""

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer

from app.controllers.recording_controller import RecordingController
from app.utils.constants import RecordingState
from app.utils.logger import AppLogger

logger = AppLogger("RecordingControllerWrapper")


class RecordingControllerWrapper:
    """
    High-level interface to RecordingController with UI integration.

    Responsibilities:
    - Start/stop recording operations
    - Handle recording errors
    - Notify UI of state changes via callbacks
    - Manage recording timer

    THREAD SAFETY:
        on_state_change is only called from start_recording() and
        stop_recording() which are always invoked from the main thread — safe.

        on_error is called from the recording thread via error_callback.
        It is marshalled to the main thread via QTimer.singleShot(0, ...)
        before the caller receives it. Safe to call Qt methods in on_error.

    Attributes:
        controller (RecordingController): Low-level recording controller
        on_state_change (callable): Callback(state, recording) on state change
        on_error (callable): Callback(error_msg) on error — main thread safe
    """

    def __init__(self, on_state_change=None, on_error=None):
        """
        Initialize recording controller wrapper.

        Args:
            on_state_change: Callback function(state, recording)
            on_error: Callback function(error_msg) — safe to update Qt widgets
        """
        self.controller     = RecordingController()
        self.on_state_change = on_state_change
        self.on_error        = on_error

        # Connect controller error callback
        self.controller.set_error_callback(self._handle_controller_error)

        logger.debug("RecordingControllerWrapper initialized")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: STATE PROPERTY AND CONVENIENCE METHODS
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def state(self):
        """Get current recording state."""
        return self.controller.state

    def is_recording(self) -> bool:
        """True if actively recording."""
        return self.controller.state == RecordingState.RECORDING

    def is_idle(self) -> bool:
        """True if idle and ready to record."""
        return self.controller.state == RecordingState.IDLE

    def is_error(self) -> bool:
        """True if controller is in error state."""
        return self.controller.state == RecordingState.ERROR

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────

    def start_recording(self):
        """
        Start a new recording.

        Returns:
            tuple: (success: bool, recording: object or None, error: str or None)
        """
        success, recording, error = self.controller.start_recording()

        if success:
            logger.info(f"Recording started: {recording.filepath}")

            if self.on_state_change:
                self.on_state_change(RecordingState.RECORDING, recording)

            return True, recording, None
        else:
            logger.error(f"Failed to start recording: {error}")
            return False, None, error

    def stop_recording(self):
        """
        Stop current recording.

        Returns:
            tuple: (success: bool, recording: object or None, error: str or None)
        """
        success, recording, error = self.controller.stop_recording()

        if success:
            logger.info(f"Recording stopped: {recording.filepath}")

            if self.on_state_change:
                self.on_state_change(RecordingState.IDLE, recording)

            return True, recording, None
        else:
            logger.error(f"Failed to stop recording: {error}")
            return False, None, error

    def get_elapsed_time(self) -> int:
        """
        Get elapsed recording time in seconds.

        Returns:
            int: Seconds elapsed (0 if not recording)
        """
        return self.controller.get_elapsed_time()

    def get_current_frame(self):
        """
        Get current video frame for preview (thread-safe).

        Returns:
            numpy.ndarray or None
        """
        return self.controller.get_current_frame()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: ERROR HANDLING
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_controller_error(self, error_msg):
        """
        Handle errors from recording controller (thread crashes, camera errors).

        CRITICAL: This method is called FROM the recording thread.
        Qt widget methods must NEVER be called directly here.

        QTimer.singleShot(0, ...) posts the call to the main event loop —
        on_error executes on the main thread where Qt operations are safe.

        Args:
            error_msg: Error message from controller
        """
        logger.error(f"Controller error: {error_msg}")

        if self.on_error:
            # Marshal to main thread — REQUIRED before any Qt UI operation
            QTimer.singleShot(0, lambda: self.on_error(error_msg))


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS: RecordingTimer
# ═══════════════════════════════════════════════════════════════════════════════

class RecordingTimer:
    """
    Manages recording timer display.

    Updates timer label every 100ms with current recording time.
    Only rewrites the label text when the displayed value changes —
    avoids redundant setText calls for the same second.

    Attributes:
        timer_label (QLabel): Qt label widget to update
        controller_wrapper (RecordingControllerWrapper): For elapsed time
        timer (QTimer): Qt timer for periodic updates
        _last_display (str): Last value written to label — avoids redundant updates
    """

    def __init__(self, timer_label, controller_wrapper):
        """
        Initialize recording timer.

        Args:
            timer_label: QLabel widget for displaying time
            controller_wrapper: RecordingControllerWrapper instance
        """
        self.timer_label         = timer_label
        self.controller_wrapper  = controller_wrapper
        self._last_display       = ""

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_display)

        logger.debug("RecordingTimer initialized")

    def start(self):
        """Start timer updates (100ms intervals)."""
        self._last_display = ""
        self.timer.start(100)
        logger.debug("Timer started")

    def stop(self):
        """Stop timer updates and reset display."""
        self.timer.stop()
        self.timer_label.setText("00:00:00")
        self._last_display = "00:00:00"
        logger.debug("Timer stopped")

    def _update_display(self):
        """
        Update timer display with current elapsed time.

        Format: HH:MM:SS
        Only calls setText when value changes — avoids 10 redundant writes
        per second when the displayed second hasn't changed yet.

        Called automatically by QTimer every 100ms.
        """
        elapsed = self.controller_wrapper.get_elapsed_time()

        hours    = elapsed // 3600
        mins     = (elapsed % 3600) // 60
        secs     = elapsed % 60
        time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

        if time_str != self._last_display:
            self.timer_label.setText(time_str)
            self._last_display = time_str


__all__ = ['RecordingControllerWrapper', 'RecordingTimer']
