"""
Recording Controller Wrapper - State Management

Wraps the RecordingController to provide high-level recording operations.
Handles state transitions, error handling, and UI updates.

Author: OT Video Dev Team
Date: February 16, 2026
Version: 2.0.0 (Refactored)
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
    
    Attributes:
        controller (RecordingController): Low-level recording controller
        state (RecordingState): Current recording state
        on_state_change (callable): Callback when state changes
        on_error (callable): Callback when error occurs
    """
    
    def __init__(self, on_state_change=None, on_error=None):
        """
        Initialize recording controller wrapper.
        
        Args:
            on_state_change: Callback function(state, recording) when state changes
            on_error: Callback function(error_msg) when error occurs
        """
        self.controller = RecordingController()
        self.on_state_change = on_state_change
        self.on_error = on_error
        
        # Connect controller error callback
        self.controller.set_error_callback(self._handle_controller_error)
        
        logger.debug("RecordingControllerWrapper initialized")
    
    @property
    def state(self):
        """Get current recording state."""
        return self.controller.state
    
    def start_recording(self):
        """
        Start a new recording.
        
        Returns:
            tuple: (success: bool, recording: object or None, error: str or None)
        
        Workflow:
        1. Call controller.start_recording()
        2. If success: Notify UI via callback
        3. If failure: Return error message
        
        Example:
            >>> success, recording, error = wrapper.start_recording()
            >>> if success:
            >>>     print(f"Recording started: {recording.filepath}")
            >>> else:
            >>>     print(f"Error: {error}")
        """
        success, recording, error = self.controller.start_recording()
        
        if success:
            logger.info(f"Recording started: {recording.filepath}")
            
            # Notify UI
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
        
        Workflow:
        1. Call controller.stop_recording()
        2. If success: Notify UI via callback
        3. If failure: Return error message
        
        Example:
            >>> success, recording, error = wrapper.stop_recording()
            >>> if success:
            >>>     print(f"Recording stopped: {recording.duration}s")
            >>> else:
            >>>     print(f"Error: {error}")
        """
        success, recording, error = self.controller.stop_recording()
        
        if success:
            logger.info(f"Recording stopped: {recording.filepath}")
            
            # Notify UI
            if self.on_state_change:
                self.on_state_change(RecordingState.IDLE, recording)
            
            return True, recording, None
        else:
            logger.error(f"Failed to stop recording: {error}")
            return False, None, error
    
    def get_elapsed_time(self):
        """
        Get elapsed recording time in seconds.
        
        Returns:
            int: Seconds elapsed (0 if not recording)
        
        Example:
            >>> elapsed = wrapper.get_elapsed_time()
            >>> print(f"Recording for {elapsed} seconds")
        """
        return self.controller.get_elapsed_time()
    
    def get_current_frame(self):
        """
        Get current video frame for preview.
        
        Returns:
            numpy.ndarray or None: Current frame (BGR) or None if unavailable
        
        Thread-safe: Can be called from UI thread.
        
        Example:
            >>> frame = wrapper.get_current_frame()
            >>> if frame is not None:
            >>>     # Display frame in preview
        """
        return self.controller.get_current_frame()
    
    def _handle_controller_error(self, error_msg):
        """
        Handle errors from recording controller (thread crashes, etc.).
        
        Args:
            error_msg: Error message from controller
        
        Called by RecordingController when recording thread crashes.
        """
        logger.error(f"Controller error: {error_msg}")
        
        # Notify UI
        if self.on_error:
            self.on_error(error_msg)


class RecordingTimer:
    """
    Manages recording timer display.
    
    Updates timer label every 100ms with current recording time.
    
    Attributes:
        timer_label (QLabel): Qt label widget to update
        controller_wrapper (RecordingControllerWrapper): For getting elapsed time
        timer (QTimer): Qt timer for periodic updates
    """
    
    def __init__(self, timer_label, controller_wrapper):
        """
        Initialize recording timer.
        
        Args:
            timer_label: QLabel widget for displaying time
            controller_wrapper: RecordingControllerWrapper instance
        """
        self.timer_label = timer_label
        self.controller_wrapper = controller_wrapper
        
        # Create Qt timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_display)
        
        logger.debug("RecordingTimer initialized")
    
    def start(self):
        """Start timer updates (100ms intervals)."""
        self.timer.start(100)  # Update every 100ms
        logger.debug("Timer started")
    
    def stop(self):
        """Stop timer updates and reset display."""
        self.timer.stop()
        self.timer_label.setText("00:00:00")
        logger.debug("Timer stopped")
    
    def _update_display(self):
        """
        Update timer display with current elapsed time.
        
        Format: HH:MM:SS
        
        Called automatically by QTimer every 100ms.
        """
        elapsed = self.controller_wrapper.get_elapsed_time()
        
        hours = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        
        time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
        self.timer_label.setText(time_str)


__all__ = ['RecordingControllerWrapper', 'RecordingTimer']
