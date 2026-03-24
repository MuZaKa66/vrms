"""
File: app/services/video_capture_service.py

Module Description:
    USB video capture service for CVBS microscope input.
    
    Works on both Windows (laptop dev) and Linux (Raspberry Pi).
    
    Professional error handling for busy medical environment:
    - Auto-detect and open camera device
    - Clear errors (device not found, busy, disconnected)
    - Auto-retry on transient failures
    - Frame capture with validation
    - Device health monitoring

Dependencies:
    - cv2 (OpenCV): Video capture
    - numpy: Frame arrays
    - config: Device settings

Author: OT Video Dev Team
Date: January 30, 2026
Version: 1.0.0
"""

import cv2
import time
import platform
from typing import Tuple, Optional, Dict
import numpy as np
from pathlib import Path

from config.app_config import VIDEO_DEVICE, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors, retry

logger = AppLogger("VideoCaptureService")


class VideoCaptureService:
    """
    USB video capture service.
    
    Captures frames from USB video device (CVBS microscope input).
    Auto-detects platform and uses appropriate backend:
    - Windows: DirectShow (CAP_DSHOW)
    - Linux/Pi: V4L2 (CAP_V4L2)
    
    Methods:
        open(): Open camera device
        close(): Close device
        read_frame(): Capture single frame
        is_available(): Check device exists
        get_info(): Get device capabilities
    
    Example:
        >>> capture = VideoCaptureService()
        >>> success, _, error = capture.open()
        >>> if success:
        ...     success, frame, error = capture.read_frame()
        ...     if success:
        ...         # Use frame
        ...         pass
        ...     capture.close()
    """
    
    def __init__(self, device_path = VIDEO_DEVICE):
        """
        Initialize video capture service.
        
        Args:
            device_path: Can be either:
                - Integer (0, 1, 2...) for Windows camera index
                - String path ("/dev/video0") for Linux device
        """
        self.device_path = device_path
        self.width = VIDEO_WIDTH
        self.height = VIDEO_HEIGHT
        self.fps = VIDEO_FPS
        self.capture = None
        self.is_open = False
        
        # Auto-detect platform and set backend
        self.is_windows = platform.system() == "Windows"
        
        logger.info(f"Video capture initialized: {device_path}")
        logger.info(f"Platform: {platform.system()}")
    
    @log_errors
    @retry(max_attempts=3, delay=1.0)
    def open(self) -> Tuple[bool, None, Optional[str]]:
        """
        Open video capture device.
        
        Auto-detects platform and uses appropriate method:
        - Windows: Uses integer device index with DirectShow
        - Linux/Pi: Uses device path with V4L2
        
        Returns:
            tuple: (success, None, error_message)
        """
        if self.is_open and self.capture is not None:
            return True, None, None
        
        try:
            # Platform-specific device checking
            if not self.is_windows:
                # Linux/Pi: Check device file exists
                if not Path(self.device_path).exists():
                    return False, None, (
                        "Camera not found. "
                        "Please check USB connection and try again."
                    )
            
            # Open device with platform-specific backend
            if self.is_windows:
                # Windows: Use DirectShow backend
                # device_path should be integer (0, 1, 2...)
                self.capture = cv2.VideoCapture(self.device_path, cv2.CAP_DSHOW)
                logger.info(f"Opening Windows camera {self.device_path} with DirectShow")
            else:
                # Linux/Pi: Use V4L2 backend
                # device_path should be string ("/dev/video0")
                self.capture = cv2.VideoCapture(self.device_path, cv2.CAP_V4L2)
                logger.info(f"Opening Linux camera {self.device_path} with V4L2")
            
            if not self.capture.isOpened():
                return False, None, (
                    "Cannot open camera. "
                    "Device may be in use. Please restart the application."
                )
            
            # Configure capture settings
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Warm up camera (discard first frames - often blank/corrupted)
            for _ in range(5):
                self.capture.read()
                time.sleep(0.05)
            
            self.is_open = True
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            
            logger.info(f"Camera opened successfully: {actual_width}x{actual_height} @ {actual_fps}fps")
            return True, None, None
        
        except Exception as e:
            logger.error(f"Camera error: {e}")
            return False, None, "Camera initialization failed. Please reconnect USB cable."
    
    @log_errors
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], Optional[str]]:
        """
        Capture single frame from camera.
        
        Returns:
            tuple: (success, frame_array, error_message)
                  frame_array is numpy array (height, width, 3) BGR format
        """
        if not self.is_open or self.capture is None:
            return False, None, "Camera not ready. Please start recording first."
        
        try:
            ret, frame = self.capture.read()
            
            if not ret or frame is None:
                return False, None, "Frame capture failed. Check camera connection."
            
            return True, frame, None
        
        except Exception as e:
            logger.error(f"Frame read error: {e}")
            return False, None, "Camera disconnected. Please reconnect."
    
    def close(self):
        """Close camera device and release resources."""
        if self.capture is not None:
            self.capture.release()
            self.capture = None
            self.is_open = False
            logger.info("Camera closed")
    
    def is_available(self) -> bool:
        """
        Check if camera device is available.
        
        Platform-specific checking:
        - Windows: Always returns True (device index always "exists")
        - Linux/Pi: Checks if device file exists
        
        Returns:
            bool: True if device available
        """
        if self.is_windows:
            # On Windows, can't check device file
            # Just return True - open() will fail properly if device doesn't exist
            return True
        else:
            # On Linux, check device file
            return Path(self.device_path).exists()
    
    def get_info(self) -> Dict:
        """
        Get current camera device information.
        
        Returns:
            dict: Camera properties (width, height, fps, is_open)
                  Empty dict if camera not open
        """
        if not self.is_open or self.capture is None:
            return {}
        
        return {
            'width': int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.capture.get(cv2.CAP_PROP_FPS)),
            'backend': 'DirectShow' if self.is_windows else 'V4L2',
            'is_open': self.is_open
        }
    
    def __del__(self):
        """Cleanup on object deletion."""
        self.close()


__all__ = ['VideoCaptureService']


# ============================================================================
# PLATFORM CONFIGURATION NOTES
# ============================================================================
#
# This service automatically adapts to the platform:
#
# WINDOWS (Laptop Development):
#   - Uses DirectShow backend (cv2.CAP_DSHOW)
#   - VIDEO_DEVICE should be integer: 0, 1, 2...
#   - Example in app_config.py:
#       VIDEO_DEVICE = 1  # USB capture device
#
# LINUX/RASPBERRY PI (Production):
#   - Uses V4L2 backend (cv2.CAP_V4L2)
#   - VIDEO_DEVICE should be string path
#   - Example in app_config.py:
#       VIDEO_DEVICE = "/dev/video0"
#
# NO CODE CHANGES NEEDED - just update app_config.py for your platform!
#
# ============================================================================
