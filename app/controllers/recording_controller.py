"""
File: app/controllers/recording_controller.py

═══════════════════════════════════════════════════════════════════════════
RECORDING CONTROLLER - Robust with User Notifications
═══════════════════════════════════════════════════════════════════════════

IMPROVEMENTS FROM PREVIOUS VERSION:
1. Thread crashes now notify user immediately
2. Error callback system for GUI notification
3. Comprehensive error recovery
4. All existing functionality preserved
5. Active temp file tracking for storage service protection

ROBUSTNESS FEATURES:
- Thread errors don't fail silently
- User always informed of recording issues
- Daemon thread can't block app exit
- Frame capture errors handled gracefully
- Active temp file tracked for cleanup protection
- force_stop() allows clean reset from any state
- stop_recording() handles both RECORDING and ERROR states

Version: 3.2.0
Date: April 9, 2026
Changelog:
    - v3.2.0: Added force_stop(), ERROR state handling in stop_recording(),
              renamed error_count → consecutive_error_count for clarity,
              null-guard in cancel_recording() for temp_video_path
    - v3.1.0: Added _active_temp_file class variable and get_active_temp_file()
    - v3.0.0: Robust error handling with user notifications
"""

import threading
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Callable
import numpy as np

from app.models.recording import Recording
from app.services.video_capture_service import VideoCaptureService
from app.services.video_encoder_service import VideoEncoderService
from app.services.storage_service import StorageService
from app.utils.logger import AppLogger
from app.utils.constants import RecordingState
from config.app_config import TEMP_DIR

logger = AppLogger("RecordingController")


class RecordingController:
    """
    Recording workflow controller with robust error handling.

    ERROR HANDLING STRATEGY:
    - Thread errors call error_callback to notify GUI
    - User sees friendly error messages
    - Recording state always consistent
    - Resources always cleaned up

    ACTIVE TEMP FILE TRACKING:
    - Tracks current temp file path for storage service
    - Prevents cleanup while recording is active

    RECOVERY:
    - force_stop() resets controller to IDLE from any state
    - stop_recording() accepts both RECORDING and ERROR states
    """

    # Class variable to track active temp file (for storage service protection)
    _active_temp_file = None

    def __init__(self):
        """Initialize recording controller."""
        self.camera   = VideoCaptureService()
        self.encoder  = VideoEncoderService()
        self.storage  = StorageService()

        self.state     = RecordingState.IDLE
        self.recording = None

        self.recording_thread    = None
        self.stop_recording_flag = False

        self.start_time      = None
        self.temp_video_path = None   # instance variable for temp file path

        # Frame storage (thread-safe)
        self.current_frame = None
        self.frame_lock    = threading.Lock()

        # ERROR CALLBACK — set by recording_screen, called when thread crashes
        self.error_callback = None

        logger.info("Recording controller initialized")

    def set_error_callback(self, callback: Callable[[str], None]):
        """
        Set callback for error notifications.

        Args:
            callback: Function to call with error message.
                      Will be called from recording thread — caller must
                      marshal to main thread before touching Qt widgets.
        """
        self.error_callback = callback
        logger.debug("Error callback set")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: START RECORDING
    # ─────────────────────────────────────────────────────────────────────────

    def start_recording(self) -> Tuple[bool, Optional[Recording], Optional[str]]:
        """
        Start video recording.

        ROBUST: All failure points return clear error messages.

        Returns:
            (success, recording_object, error_message)
        """
        if self.state != RecordingState.IDLE:
            return False, None, "Recording already in progress"

        self.state = RecordingState.CHECKING

        # Check storage
        success, status, error = self.storage.get_storage_status()
        if not success:
            self.state = RecordingState.ERROR
            logger.error(f"Storage check failed: {error}")
            return False, None, f"Storage check failed: {error}"

        if status['free_gb'] < 1.0:
            self.state = RecordingState.ERROR
            logger.warning(f"Insufficient storage: {status['free_gb']:.1f} GB")
            return False, None, f"Insufficient storage: {status['free_gb']:.1f} GB free (need 1 GB)"

        # Create Recording
        self.recording = Recording.create_new()
        logger.info(f"Created recording: {self.recording.filename}")

        self.state = RecordingState.STARTING

        # Open Camera
        success, camera_info, error = self.camera.open()
        if not success:
            self.state = RecordingState.ERROR
            logger.error(f"Camera failed: {error}")
            return False, None, f"Camera error: {error}"

        logger.info(f"Camera opened: {camera_info}")

        # Start Encoder
        self.temp_video_path = str(Path(TEMP_DIR) / self.recording.filename)

        # ── Register active temp file for storage service protection ──────────
        RecordingController._active_temp_file = self.temp_video_path
        logger.debug(f"Active temp file registered: {self.temp_video_path}")

        success, _, error = self.encoder.start_encoding(self.temp_video_path)
        if not success:
            RecordingController._active_temp_file = None
            self.camera.close()
            self.state = RecordingState.ERROR
            logger.error(f"Encoder failed: {error}")
            return False, None, f"Video encoder error: {error}"

        logger.info(f"Encoder started: {self.temp_video_path}")

        # Start Recording Thread (DAEMON — won't block app exit)
        self.stop_recording_flag = False
        self.start_time          = time.time()

        self.recording_thread = threading.Thread(
            target=self._recording_loop,
            daemon=True,
            name="RecordingLoop"
        )
        self.recording_thread.start()

        self.state = RecordingState.RECORDING

        logger.info("Recording started successfully")
        return True, self.recording, None

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING LOOP (runs in background thread)
    # ─────────────────────────────────────────────────────────────────────────

    def _recording_loop(self):
        """
        Main recording loop with robust error handling.

        ROBUST FEATURES:
        - consecutive_error_count resets on every good frame (not cumulative)
        - Thread crashes notify user via callback (marshalled to main thread by wrapper)
        - Error counter prevents infinite retry loops
        - Resources remain for force_stop() / stop_recording() to clean up
        """
        frame_count              = 0
        consecutive_error_count  = 0      # resets on each good frame
        max_consecutive_errors   = 10

        logger.debug("Recording loop started")

        while not self.stop_recording_flag:
            try:
                # Capture frame
                success, frame, error = self.camera.read_frame()

                if not success:
                    consecutive_error_count += 1
                    logger.error(
                        f"Frame capture failed (#{consecutive_error_count}): {error}"
                    )

                    if consecutive_error_count >= max_consecutive_errors:
                        logger.error(
                            f"Too many consecutive frame errors "
                            f"({consecutive_error_count}), stopping"
                        )
                        self.state = RecordingState.ERROR

                        if self.error_callback:
                            try:
                                self.error_callback(
                                    f"Recording stopped: Camera error\n\n"
                                    f"{error}\n\n"
                                    f"Video may be incomplete."
                                )
                            except Exception:
                                pass  # never crash inside thread on callback error

                        break

                    time.sleep(0.1)   # brief pause before retry
                    continue

                # ── Good frame ────────────────────────────────────────────────
                consecutive_error_count = 0   # reset on success

                # Store frame for preview (thread-safe)
                with self.frame_lock:
                    self.current_frame = frame.copy()

                # Send frame to encoder
                success, _, error = self.encoder.write_frame(frame)

                if not success:
                    logger.error(f"Frame encoding failed: {error}")
                    self.state = RecordingState.ERROR

                    if self.error_callback:
                        try:
                            self.error_callback(
                                f"Recording stopped: Encoder error\n\n"
                                f"{error}\n\n"
                                f"Video may be corrupted."
                            )
                        except Exception:
                            pass

                    break

                frame_count += 1

                # ~30 fps
                time.sleep(0.001)

            except Exception as e:
                logger.error(f"Recording loop exception: {e}", exc_info=True)
                self.state = RecordingState.ERROR

                if self.error_callback:
                    try:
                        self.error_callback(
                            f"Recording stopped unexpectedly:\n\n"
                            f"{str(e)}\n\n"
                            f"Video may be incomplete or corrupted."
                        )
                    except Exception:
                        pass

                break

        logger.debug(f"Recording loop ended. Frames captured: {frame_count}")
        # NOTE: Encoder and camera are NOT closed here.
        # force_stop() or stop_recording() handle cleanup — keeps resource
        # management in one place regardless of how the loop exits.

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: STOP RECORDING
    # ─────────────────────────────────────────────────────────────────────────

    def stop_recording(self) -> Tuple[bool, Optional[Recording], Optional[str]]:
        """
        Stop recording and save video.

        Accepts both RECORDING and ERROR states — allows clean stop after
        a camera/encoder error without requiring force_stop().

        Returns:
            (success, recording_object, error_message)
        """
        if self.state not in (RecordingState.RECORDING, RecordingState.ERROR):
            return False, None, "Not currently recording"

        self.state = RecordingState.STOPPING
        logger.info("Stopping recording...")

        # Stop thread
        self.stop_recording_flag = True

        if self.recording_thread:
            self.recording_thread.join(timeout=5.0)
            if self.recording_thread.is_alive():
                logger.warning("Recording thread did not stop gracefully")

        # Stop encoder
        success, stats, error = self.encoder.stop_encoding()
        if not success:
            logger.error(f"Encoder stop failed: {error}")
            self.camera.close()
            self.state = RecordingState.ERROR
            RecordingController._active_temp_file = None
            return False, None, f"Failed to finalize video: {error}"

        logger.info(f"Encoder stopped: {stats}")

        # Close camera
        self.camera.close()
        logger.info("Camera closed")

        # Calculate duration
        if self.start_time:
            duration = int(time.time() - self.start_time)
            self.recording.duration_seconds = duration
            logger.debug(f"Recording duration: {duration} seconds")

        self.state = RecordingState.SAVING

        # Save to storage
        success, final_path, error = self.storage.save_recording(
            self.temp_video_path,
            self.recording
        )

        # ── Clear active temp file (recording complete) ────────────────────
        RecordingController._active_temp_file = None
        logger.debug("Active temp file cleared")

        if not success:
            self.state = RecordingState.ERROR
            logger.error(f"Storage save failed: {error}")
            return False, None, f"Failed to save video: {error}"

        self.recording.filepath = final_path
        logger.info(f"Video saved: {final_path}")

        # Save to database
        from app.services.database_service import DatabaseService
        db = DatabaseService()

        success, rec_id, error = db.create_recording(self.recording)
        if not success:
            logger.error(f"Database save failed: {error}")
            # Video is saved — don't fail the operation, log for debugging
        else:
            self.recording.id = rec_id
            logger.info(f"Recording saved to database: ID={rec_id}")

        # Cleanup
        with self.frame_lock:
            self.current_frame = None

        finished_recording = self.recording

        self.recording    = None
        self.start_time   = None
        self.state        = RecordingState.IDLE

        logger.info("Recording stopped successfully")
        return True, finished_recording, None

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: FORCE STOP (emergency reset from any state)
    # ─────────────────────────────────────────────────────────────────────────

    def force_stop(self):
        """
        Force-stop all resources and reset to IDLE — safe to call in any state.

        Used by _recover_from_error() in recording_screen when the controller
        is stuck in ERROR, STOPPING, or any unexpected state.

        Does NOT attempt to save the video — this is emergency cleanup only.
        """
        logger.info(f"Force stop called (current state: {self.state})")

        self.stop_recording_flag = True

        # Stop recording thread
        try:
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)
        except Exception as e:
            logger.warning(f"Thread join failed during force_stop: {e}")

        # Stop encoder (ignore errors — may already be stopped)
        try:
            self.encoder.stop_encoding()
        except Exception as e:
            logger.warning(f"Encoder stop failed during force_stop: {e}")

        # Close camera (ignore errors — may already be closed)
        try:
            self.camera.close()
        except Exception as e:
            logger.warning(f"Camera close failed during force_stop: {e}")

        # Clear active temp file
        RecordingController._active_temp_file = None

        # Clear frame buffer
        with self.frame_lock:
            self.current_frame = None

        # Reset all state
        self.recording           = None
        self.start_time          = None
        self.temp_video_path     = None
        self.stop_recording_flag = False
        self.recording_thread    = None
        self.state               = RecordingState.IDLE

        logger.info("Force stop complete — controller reset to IDLE")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: CANCEL RECORDING
    # ─────────────────────────────────────────────────────────────────────────

    def cancel_recording(self) -> Tuple[bool, Optional[str]]:
        """
        Cancel recording and discard video.

        Returns:
            (success, error_message)
        """
        if self.state != RecordingState.RECORDING:
            return False, "Not currently recording"

        logger.info("Cancelling recording...")

        self.stop_recording_flag = True
        if self.recording_thread:
            self.recording_thread.join(timeout=5.0)

        self.encoder.stop_encoding()
        self.camera.close()

        RecordingController._active_temp_file = None

        # Delete temp file — null-guard: temp_video_path may be None if
        # recording failed before encoder started
        if self.temp_video_path:
            try:
                temp_path = Path(self.temp_video_path)
                if temp_path.exists():
                    temp_path.unlink()
                    logger.debug(f"Deleted temp file: {self.temp_video_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

        # Cleanup
        with self.frame_lock:
            self.current_frame = None

        self.recording    = None
        self.start_time   = None
        self.state        = RecordingState.IDLE

        logger.info("Recording cancelled")
        return True, None

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: GETTERS / STATUS
    # ─────────────────────────────────────────────────────────────────────────

    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get latest frame for GUI preview (thread-safe).

        Returns:
            Frame copy or None
        """
        if self.state != RecordingState.RECORDING:
            return None

        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def get_elapsed_time(self) -> int:
        """Get elapsed recording time in seconds."""
        if self.state != RecordingState.RECORDING or not self.start_time:
            return 0
        return int(time.time() - self.start_time)

    def get_recording_status(self) -> Dict:
        """Get current recording status."""
        return {
            'state':            self.state,
            'is_recording':     self.state == RecordingState.RECORDING,
            'elapsed_seconds':  self.get_elapsed_time(),
            'filename':         self.recording.filename if self.recording else None,
            'has_current_frame': self.current_frame is not None,
        }

    @classmethod
    def get_active_temp_file(cls):
        """
        Get the currently active temp file path.

        Used by storage service to protect active recording files from cleanup.

        Returns:
            str or None: Path to active temp file, or None if no active recording
        """
        return cls._active_temp_file


__all__ = ['RecordingController']
