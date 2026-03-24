"""
Preview Handler - Video Preview Rendering

Handles real-time video preview display during recording.
Optimized for performance with frame throttling and efficient scaling.

Key Features:
- Frame throttling (shows every Nth frame to reduce CPU)
- Efficient downscaling for large video sources
- Double-buffered rendering (prevents flicker)
- Thread-safe frame retrieval from recording controller

Author: OT Video Dev Team
Date: February 16, 2026
Version: 2.0.0 (Refactored)
"""

import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor

from app.utils.constants import RecordingState
from app.utils.logger import AppLogger
from .design_constants import COLORS, SIZES

logger = AppLogger("PreviewHandler")


class PreviewHandler:
    """
    Manages video preview display during recording.
    
    Handles:
    - Frame retrieval from recording controller
    - Frame rate throttling for performance
    - Image scaling and rendering
    - Double-buffered updates (flicker-free)
    
    Attributes:
        preview_label (QLabel): Qt label widget for displaying preview
        preview_buffer (QPixmap): Double buffer for flicker-free rendering
        controller: Recording controller instance
        frame_counter (int): Frame counter for throttling
        preview_skip_target (int): Show every Nth frame
    """
    
    def __init__(self, preview_label, preview_buffer, controller, throttle=3):
        """
        Initialize preview handler.
        
        Args:
            preview_label: Qt QLabel widget to display preview
            preview_buffer: QPixmap buffer for double buffering
            controller: RecordingController instance
            throttle: Show every Nth frame (default 3 = ~10fps from 30fps)
        """
        self.preview_label = preview_label
        self.preview_buffer = preview_buffer
        self.controller = controller
        self.frame_counter = 0
        self.preview_skip_target = throttle
        
        logger.debug(f"PreviewHandler initialized (throttle: every {throttle} frames)")
    
    def update_preview(self):
        """
        Update preview with latest frame from recording controller.
        
        OPTIMIZATION STRATEGY:
        1. Frame throttling - only show every Nth frame
        2. Downscale large frames before converting to Qt
        3. Use double buffering to prevent flicker
        4. Center scaled image in preview area
        
        PERFORMANCE:
        - Full HD (1920x1080) → ~5ms per update
        - SD (720x480) → ~2ms per update
        - With throttle=3 at 30fps → ~100ms between updates (10fps preview)
        
        Called by: QTimer at 100ms intervals
        """
        # Only update when recording
        if self.controller.state != RecordingState.RECORDING:
            return
        
        # Throttle frame rate (performance optimization)
        self.frame_counter += 1
        if self.frame_counter % self.preview_skip_target != 0:
            return
        
        # Get latest frame from controller (thread-safe)
        frame = self.controller.get_current_frame()
        if frame is None:
            return
        
        try:
            self._render_frame(frame)
        except Exception as e:
            logger.error(f"Preview update failed: {e}")
    
    def _render_frame(self, frame):
        """
        Render OpenCV frame to Qt preview widget.
        
        RENDERING PIPELINE:
        1. Get original frame dimensions
        2. Calculate target size (fit within preview area)
        3. Downscale if needed (performance)
        4. Convert BGR → RGB (OpenCV to Qt)
        5. Create QImage from numpy array
        6. Scale to exact preview size
        7. Draw centered on double buffer
        8. Update label widget
        
        Args:
            frame: OpenCV frame (BGR numpy array)
        """
        # Get original frame dimensions
        h, w = frame.shape[:2]
        
        # Target preview size
        target_w, target_h = SIZES['preview']
        
        # Calculate scaling factor
        scale = min(target_w / w, target_h / h)
        
        # Downscale before converting to Qt (performance optimization)
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            small_frame = cv2.resize(
                frame, 
                (new_w, new_h), 
                interpolation=cv2.INTER_NEAREST  # Fastest interpolation
            )
        else:
            small_frame = frame
        
        # Convert BGR (OpenCV) to RGB (Qt)
        rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        
        # Create QImage from numpy array
        # CRITICAL: Must specify bytes_per_line for proper stride
        bytes_per_line = 3 * w
        q_img = QImage(
            rgb.data,           # Raw pixel data
            w,                  # Width
            h,                  # Height  
            bytes_per_line,     # Bytes per scan line
            QImage.Format_RGB888  # 24-bit RGB format
        )
        
        # Convert to pixmap and scale to fit preview
        pixmap = QPixmap.fromImage(q_img)
        scaled = pixmap.scaled(
            target_w - 4,  # Leave 2px border margin
            target_h - 4,
            Qt.KeepAspectRatio,      # Maintain aspect ratio
            Qt.SmoothTransformation  # High-quality scaling
        )
        
        # Draw onto double buffer (prevents flicker)
        self.preview_buffer.fill(QColor(COLORS['preview_bg']))
        painter = QPainter(self.preview_buffer)
        
        # Center the scaled image
        x = (target_w - scaled.width()) // 2
        y = (target_h - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        
        # Update the preview label widget
        self.preview_label.setPixmap(self.preview_buffer)
    
    def clear_preview(self):
        """
        Clear the preview display (show black background).
        
        Called when:
        - Recording stops
        - Screen is reset
        - Error occurs
        """
        target_w, target_h = SIZES['preview']
        self.preview_buffer = QPixmap(target_w, target_h)
        self.preview_buffer.fill(QColor(COLORS['preview_bg']))
        self.preview_label.setPixmap(self.preview_buffer)
        self.frame_counter = 0
        logger.debug("Preview cleared")
    
    def set_throttle(self, throttle):
        """
        Change frame throttling rate.
        
        Args:
            throttle: Show every Nth frame (1=all frames, 3=every 3rd, etc.)
        """
        self.preview_skip_target = throttle
        logger.debug(f"Preview throttle set to: every {throttle} frames")


__all__ = ['PreviewHandler']
