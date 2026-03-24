"""
File: app/services/video_encoder_service.py

DUAL-MODE VIDEO ENCODER
========================
Supports both OpenCV and FFmpeg encoding with simple config switch.

MODE SELECTION in config/app_config.py:
    USE_OPENCV_ENCODER = True   # Simple, proven, cross-platform
    USE_OPENCV_ENCODER = False  # Advanced, optimized, Pi hardware

Author: OT Video Dev Team
Date: February 5, 2026
Version: 2.0.0 (Dual-mode)
"""

import cv2
import subprocess
import time
import platform
from pathlib import Path
from typing import Tuple, Optional, Dict
import numpy as np

from config.app_config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_ENCODER,
    VIDEO_BITRATE, USE_OPENCV_ENCODER
)
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors

logger = AppLogger("VideoEncoderService")


class VideoEncoderService:
    """
    Dual-mode video encoder service.
    
    Automatically uses OpenCV or FFmpeg based on USE_OPENCV_ENCODER setting.
    
    OpenCV Mode (USE_OPENCV_ENCODER = True):
        - Simple, reliable, cross-platform
        - Uses cv2.VideoWriter
        - Great quality, slightly larger files
        - Recommended for development/testing
    
    FFmpeg Mode (USE_OPENCV_ENCODER = False):
        - Advanced control, smaller files
        - Uses FFmpeg subprocess + pipe
        - Hardware encoding on Pi
        - Recommended for production on Pi
    
    Methods:
        start_encoding(output_path): Begin encoding
        write_frame(frame): Add frame to video
        stop_encoding(): Finalize video
    """
    
    def __init__(self):
        """Initialize encoder in selected mode."""
        self.mode = "OpenCV" if USE_OPENCV_ENCODER else "FFmpeg"
        self.is_encoding = False
        self.output_path = None
        self.frame_count = 0
        self.start_time = None
        
        # Mode-specific objects
        self.cv_writer = None      # OpenCV VideoWriter
        self.ffmpeg_process = None # FFmpeg subprocess
        
        logger.info(f"Video encoder initialized: {self.mode} mode")
    
    @log_errors
    def start_encoding(self, output_path: str) -> Tuple[bool, None, Optional[str]]:
        """
        Start encoding video.
        
        Args:
            output_path: Where to save video file
        
        Returns:
            tuple: (success, None, error_message)
        """
        if self.is_encoding:
            return False, None, "Encoder already running"
        
        self.output_path = output_path
        self.frame_count = 0
        self.start_time = time.time()
        
        try:
            if USE_OPENCV_ENCODER:
                return self._start_opencv_encoding()
            else:
                return self._start_ffmpeg_encoding()
        
        except Exception as e:
            logger.error(f"Start encoding error ({self.mode}): {e}")
            return False, None, f"Failed to start {self.mode} encoder"
    
    def _start_opencv_encoding(self) -> Tuple[bool, None, Optional[str]]:
        """Start OpenCV VideoWriter."""
        try:
            # Ensure output directory exists
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Choose codec based on platform
            if platform.system() == "Windows":
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MPEG-4
            else:
                fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 (hardware on Pi)
            
            # Create VideoWriter
            self.cv_writer = cv2.VideoWriter(
                self.output_path,
                fourcc,
                VIDEO_FPS,
                (VIDEO_WIDTH, VIDEO_HEIGHT)
            )
            
            if not self.cv_writer.isOpened():
                return False, None, "Failed to initialize OpenCV encoder"
            
            self.is_encoding = True
            logger.info(f"OpenCV encoding started: {self.output_path}")
            return True, None, None
        
        except Exception as e:
            logger.error(f"OpenCV encoder error: {e}")
            return False, None, "OpenCV encoder initialization failed"
    
    def _start_ffmpeg_encoding(self) -> Tuple[bool, None, Optional[str]]:
        """Start FFmpeg subprocess."""
        try:
            # Ensure output directory exists
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # FFmpeg command
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', f'{VIDEO_WIDTH}x{VIDEO_HEIGHT}',
                '-r', str(VIDEO_FPS),
                '-i', '-',  # stdin
                '-c:v', VIDEO_ENCODER,
                '-b:v', VIDEO_BITRATE,
                '-pix_fmt', 'yuv420p',
                self.output_path
            ]
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.is_encoding = True
            logger.info(f"FFmpeg encoding started: {self.output_path}")
            return True, None, None
        
        except Exception as e:
            logger.error(f"FFmpeg encoder error: {e}")
            return False, None, "FFmpeg encoder initialization failed"
    
    @log_errors
    def write_frame(self, frame: np.ndarray) -> Tuple[bool, None, Optional[str]]:
        """
        Write single frame to video.
        
        Args:
            frame: numpy array (height, width, 3) BGR format
        
        Returns:
            tuple: (success, None, error_message)
        """
        if not self.is_encoding:
            return False, None, "Encoder not started"
        
        try:
            if USE_OPENCV_ENCODER:
                return self._write_frame_opencv(frame)
            else:
                return self._write_frame_ffmpeg(frame)
        
        except Exception as e:
            logger.error(f"Write frame error ({self.mode}): {e}")
            return False, None, "Frame write failed"
    
    def _write_frame_opencv(self, frame: np.ndarray) -> Tuple[bool, None, Optional[str]]:
        """Write frame using OpenCV."""
        try:
            if self.cv_writer is None:
                return False, None, "OpenCV writer not initialized"
            
            self.cv_writer.write(frame)
            self.frame_count += 1
            return True, None, None
        
        except Exception as e:
            logger.error(f"OpenCV write error: {e}")
            return False, None, "OpenCV write failed"
    
    def _write_frame_ffmpeg(self, frame: np.ndarray) -> Tuple[bool, None, Optional[str]]:
        """Write frame using FFmpeg pipe."""
        try:
            if self.ffmpeg_process is None or self.ffmpeg_process.stdin is None:
                return False, None, "FFmpeg process not ready"
            
            self.ffmpeg_process.stdin.write(frame.tobytes())
            self.frame_count += 1
            return True, None, None
        
        except BrokenPipeError:
            logger.error("FFmpeg pipe broken")
            return False, None, "Encoding failed. Video may be corrupted."
        except Exception as e:
            logger.error(f"FFmpeg write error: {e}")
            return False, None, "FFmpeg write failed"
    
    @log_errors
    def stop_encoding(self) -> Tuple[bool, Dict, Optional[str]]:
        """
        Stop encoding and finalize video file.
        
        Returns:
            tuple: (success, stats_dict, error_message)
        """
        if not self.is_encoding:
            return False, {}, "Not encoding"
        
        try:
            if USE_OPENCV_ENCODER:
                return self._stop_opencv_encoding()
            else:
                return self._stop_ffmpeg_encoding()
        
        except Exception as e:
            logger.error(f"Stop encoding error ({self.mode}): {e}")
            return False, {}, "Failed to finalize video"
    
    def _stop_opencv_encoding(self) -> Tuple[bool, Dict, Optional[str]]:
        """Stop OpenCV encoding."""
        try:
            if self.cv_writer:
                self.cv_writer.release()
                self.cv_writer = None
            
            self.is_encoding = False
            duration = time.time() - self.start_time if self.start_time else 0
            
            # Get file size
            file_size = 0
            if Path(self.output_path).exists():
                file_size = Path(self.output_path).stat().st_size
            
            stats = {
                'frame_count': self.frame_count,
                'duration_seconds': int(duration),
                'output_path': self.output_path,
                'file_size_bytes': file_size,
                'file_size_mb': file_size / (1024**2),
                'encoder': 'OpenCV'
            }
            
            logger.info(
                f"OpenCV encoding complete: {self.frame_count} frames, "
                f"{stats['file_size_mb']:.2f} MB"
            )
            return True, stats, None
        
        except Exception as e:
            logger.error(f"OpenCV stop error: {e}")
            return False, {}, "Failed to finalize OpenCV video"
    
    def _stop_ffmpeg_encoding(self) -> Tuple[bool, Dict, Optional[str]]:
        """Stop FFmpeg encoding."""
        try:
            # Close stdin
            if self.ffmpeg_process and self.ffmpeg_process.stdin:
                self.ffmpeg_process.stdin.close()
            
            # Wait for FFmpeg
            if self.ffmpeg_process:
                self.ffmpeg_process.wait(timeout=10)
            
            self.is_encoding = False
            duration = time.time() - self.start_time if self.start_time else 0
            
            # Get file size
            file_size = 0
            if Path(self.output_path).exists():
                file_size = Path(self.output_path).stat().st_size
            
            stats = {
                'frame_count': self.frame_count,
                'duration_seconds': int(duration),
                'output_path': self.output_path,
                'file_size_bytes': file_size,
                'file_size_mb': file_size / (1024**2),
                'encoder': 'FFmpeg'
            }
            
            logger.info(
                f"FFmpeg encoding complete: {self.frame_count} frames, "
                f"{stats['file_size_mb']:.2f} MB"
            )
            return True, stats, None
        
        except subprocess.TimeoutExpired:
            if self.ffmpeg_process:
                self.ffmpeg_process.kill()
            return False, {}, "FFmpeg timeout. Video may be incomplete."
        except Exception as e:
            logger.error(f"FFmpeg stop error: {e}")
            return False, {}, "Failed to finalize FFmpeg video"
    
    def get_status(self) -> Dict:
        """Get current encoding status."""
        return {
            'is_encoding': self.is_encoding,
            'frame_count': self.frame_count,
            'mode': self.mode,
            'output_path': self.output_path
        }
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.is_encoding:
            try:
                self.stop_encoding()
            except:
                pass


__all__ = ['VideoEncoderService']


# ============================================================================
# MODE SELECTION GUIDE
# ============================================================================
#
# In config/app_config.py, set:
#
# USE_OPENCV_ENCODER = True
#   - For: Laptop development, testing, debugging
#   - Pros: Simple, reliable, works everywhere
#   - Cons: Slightly larger files (~10-20%)
#
# USE_OPENCV_ENCODER = False
#   - For: Production on Raspberry Pi
#   - Pros: Smaller files, hardware encoding
#   - Cons: More complex, platform-specific
#
# You can switch anytime by changing one line in config!
#
# ============================================================================
