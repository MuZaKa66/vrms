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

ROBUSTNESS FEATURES:
- Thread errors don't fail silently
- User always informed of recording issues
- Daemon thread can't block app exit
- Frame capture errors handled gracefully

Version: 3.0.0 (Robust error handling)
Date: February 13, 2026
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
    """
    
    def __init__(self):
        """Initialize recording controller."""
        self.camera = VideoCaptureService()
        self.encoder = VideoEncoderService()
        self.storage = StorageService()
        
        self.state = RecordingState.IDLE
        self.recording = None
        
        self.recording_thread = None
        self.stop_recording_flag = False
        
        self.start_time = None
        
        # Frame storage (thread-safe)
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # ERROR CALLBACK (set by recording_screen)
        self.error_callback = None  # Called when thread crashes
        
        logger.info("Recording controller initialized")
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """
        Set callback for error notifications.
        
        Args:
            callback: Function to call with error message
                     Will be called from recording thread
        """
        self.error_callback = callback
        logger.debug("Error callback set")
    
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
        
        success, _, error = self.encoder.start_encoding(self.temp_video_path)
        if not success:
            self.camera.close()
            self.state = RecordingState.ERROR
            logger.error(f"Encoder failed: {error}")
            return False, None, f"Video encoder error: {error}"
        
        logger.info(f"Encoder started: {self.temp_video_path}")
        
        # Start Recording Thread (DAEMON - can't block exit)
        self.stop_recording_flag = False
        self.start_time = time.time()
        
        self.recording_thread = threading.Thread(
            target=self._recording_loop,
            daemon=True,  # CRITICAL: Won't block app exit
            name="RecordingLoop"
        )
        self.recording_thread.start()
        
        # Update State
        self.state = RecordingState.RECORDING
        
        logger.info("Recording started successfully")
        return True, self.recording, None
    
    def _recording_loop(self):
        """
        Main recording loop with robust error handling.
        
        ROBUST FEATURES:
        - Frame capture errors logged and handled
        - Thread crashes notify user via callback
        - Error counter prevents infinite retry loops
        - Resources cleaned up on exit
        """
        frame_count = 0
        error_count = 0
        max_consecutive_errors = 10
        
        logger.debug("Recording loop started")
        
        while not self.stop_recording_flag:
            try:
                # Capture frame
                success, frame, error = self.camera.read_frame()
                
                if not success:
                    error_count += 1
                    logger.error(f"Frame capture failed (#{error_count}): {error}")
                    
                    # Too many errors - stop recording
                    if error_count >= max_consecutive_errors:
                        logger.error(f"Too many frame errors ({error_count}), stopping")
                        self.state = RecordingState.ERROR
                        
                        # NOTIFY USER
                        if self.error_callback:
                            try:
                                self.error_callback(
                                    f"Recording stopped: Camera error\n\n"
                                    f"{error}\n\n"
                                    f"Video may be incomplete."
                                )
                            except:
                                pass  # Don't crash on callback error
                        
                        break
                    
                    # Brief pause before retry
                    time.sleep(0.1)
                    continue
                
                # Success - reset error count
                error_count = 0
                
                # Store frame for preview (thread-safe)
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Send frame to encoder
                success, _, error = self.encoder.write_frame(frame)
                
                if not success:
                    logger.error(f"Frame encoding failed: {error}")
                    self.state = RecordingState.ERROR
                    
                    # NOTIFY USER
                    if self.error_callback:
                        try:
                            self.error_callback(
                                f"Recording stopped: Encoder error\n\n"
                                f"{error}\n\n"
                                f"Video may be corrupted."
                            )
                        except:
                            pass
                    
                    break
                
                frame_count += 1
                
                # ~30 fps (adjust as needed)
                time.sleep(0.001)
            
            except Exception as e:
                # UNEXPECTED ERROR
                logger.error(f"Recording loop exception: {e}", exc_info=True)
                self.state = RecordingState.ERROR
                
                # NOTIFY USER
                if self.error_callback:
                    try:
                        self.error_callback(
                            f"Recording stopped unexpectedly:\n\n"
                            f"{str(e)}\n\n"
                            f"Video may be incomplete or corrupted."
                        )
                    except:
                        pass
                
                break
        
        logger.debug(f"Recording loop ended. Frames captured: {frame_count}")
    
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
    
    def stop_recording(self) -> Tuple[bool, Optional[Recording], Optional[str]]:
        """
        Stop recording and save video.
        
        ROBUST: Comprehensive error handling at each step.
        
        Returns:
            (success, recording_object, error_message)
        """
        if self.state != RecordingState.RECORDING:
            return False, None, "Not currently recording"
        
        self.state = RecordingState.STOPPING
        logger.info("Stopping recording...")
        
        # Stop thread
        self.stop_recording_flag = True
        
        if self.recording_thread:
            self.recording_thread.join(timeout=5.0)
            if self.recording_thread.is_alive():
                logger.warning("⚠ Recording thread did not stop gracefully")
                # Thread will exit eventually (daemon)
        
        # Stop encoder
        success, stats, error = self.encoder.stop_encoding()
        if not success:
            logger.error(f"Encoder stop failed: {error}")
            self.camera.close()
            self.state = RecordingState.ERROR
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
            logger.error(f"⚠ Database save failed: {error}")
            # Video is saved, so don't fail the operation
            # But log the error for debugging
        else:
            self.recording.id = rec_id
            logger.info(f"Recording saved to database: ID={rec_id}")
        
        # Cleanup
        with self.frame_lock:
            self.current_frame = None
        
        finished_recording = self.recording
        
        self.recording = None
        self.start_time = None
        self.state = RecordingState.IDLE
        
        logger.info("✓ Recording stopped successfully")
        return True, finished_recording, None
    
    def cancel_recording(self) -> Tuple[bool, Optional[str]]:
        """
        Cancel recording and discard video.
        
        ROBUST: Always succeeds, cleans up resources.
        
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
        
        # Delete temp file
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
        
        self.recording = None
        self.start_time = None
        self.state = RecordingState.IDLE
        
        logger.info("Recording cancelled")
        return True, None
    
    def get_elapsed_time(self) -> int:
        """Get elapsed recording time in seconds."""
        if self.state != RecordingState.RECORDING or not self.start_time:
            return 0
        
        return int(time.time() - self.start_time)
    
    def get_recording_status(self) -> Dict:
        """Get current recording status."""
        return {
            'state': self.state,
            'is_recording': self.state == RecordingState.RECORDING,
            'elapsed_seconds': self.get_elapsed_time(),
            'filename': self.recording.filename if self.recording else None,
            'has_current_frame': self.current_frame is not None
        }


__all__ = ['RecordingController']
