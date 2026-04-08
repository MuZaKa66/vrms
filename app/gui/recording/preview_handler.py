"""
File: app/gui/recording/preview_handler.py

Preview Handler - Video Preview Rendering

Handles real-time video preview display during recording.
Optimized for performance with frame throttling and efficient scaling.

Key Features:
- Frame throttling (shows every Nth frame to reduce CPU)
- Efficient downscaling for large video sources
- Double-buffered rendering (prevents flicker)
- Thread-safe frame retrieval from recording controller
- QPainter always closed via try/finally (prevents QBackingStore crash)
- clear_preview() fills existing buffer in-place (no stale reference issue)
- INTER_LINEAR interpolation for better visual quality on 7" display

Author: OT Video Dev Team
Date: April 9, 2026
Version: 2.1.0
Changelog:
    - v2.1.0: QPainter wrapped in try/finally to prevent unclosed painter crash.
              clear_preview() fills buffer in-place instead of reassigning —
              prevents stale reference in recording_screen._preview_buffer.
              INTER_NEAREST → INTER_LINEAR for better image quality on Pi 4.
    - v2.0.0: Refactored
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
        self.preview_label      = preview_label
        self.preview_buffer     = preview_buffer
        self.controller         = controller
        self.frame_counter      = 0
        self.preview_skip_target = throttle

        logger.debug(f"PreviewHandler initialized (throttle: every {throttle} frames)")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: PREVIEW UPDATE
    # ─────────────────────────────────────────────────────────────────────────

    def update_preview(self):
        """
        Update preview with latest frame from recording controller.

        OPTIMIZATION STRATEGY:
        1. Frame throttling — only show every Nth frame
        2. Downscale large frames before converting to Qt
        3. Use double buffering to prevent flicker
        4. Center scaled image in preview area

        Called by: QTimer at 100ms intervals
        """
        # Only update when recording
        if self.controller.state != RecordingState.RECORDING:
            return

        # Throttle frame rate
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
        3. Downscale if needed
        4. Convert BGR → RGB
        5. Create QImage from numpy array
        6. Scale to preview size
        7. Draw centered on double buffer — painter ALWAYS closed via try/finally
        8. Update label widget

        Args:
            frame: OpenCV frame (BGR numpy array)
        """
        h, w = frame.shape[:2]

        target_w, target_h = SIZES['preview']

        scale = min(target_w / w, target_h / h)

        # Downscale before converting to Qt (performance optimization)
        # INTER_LINEAR: better quality than INTER_NEAREST, minimal extra cost on Pi 4
        if scale < 1.0:
            new_w     = int(w * scale)
            new_h     = int(h * scale)
            small_frame = cv2.resize(
                frame,
                (new_w, new_h),
                interpolation=cv2.INTER_LINEAR
            )
        else:
            small_frame = frame

        # Convert BGR (OpenCV) to RGB (Qt)
        rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]

        # Create QImage from numpy array
        bytes_per_line = 3 * w
        q_img = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

        # Scale to fit preview
        pixmap = QPixmap.fromImage(q_img)
        scaled = pixmap.scaled(
            target_w - 4,
            target_h - 4,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # ── Draw onto double buffer ────────────────────────────────────────────
        # CRITICAL: painter.end() must ALWAYS be called.
        # try/finally guarantees this even if drawPixmap() throws.
        # An unclosed painter causes QBackingStore::endPaint() crash.
        self.preview_buffer.fill(QColor(COLORS['preview_bg']))
        painter = QPainter(self.preview_buffer)
        try:
            x = (target_w - scaled.width()) // 2
            y = (target_h - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        finally:
            painter.end()   # always executes — even on exception

        # Update the preview label widget
        self.preview_label.setPixmap(self.preview_buffer)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: CLEAR PREVIEW
    # ─────────────────────────────────────────────────────────────────────────

    def clear_preview(self):
        """
        Clear the preview display (show black background).

        IMPORTANT: Fills the existing buffer IN-PLACE rather than reassigning
        self.preview_buffer to a new QPixmap. This preserves the reference held
        by recording_screen._preview_buffer — prevents stale buffer mismatch.

        Called when:
        - Recording stops
        - Screen is reset
        - Error occurs
        """
        self.preview_buffer.fill(QColor(COLORS['preview_bg']))
        self.preview_label.setPixmap(self.preview_buffer)
        self.frame_counter = 0
        logger.debug("Preview cleared")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: CONFIGURATION
    # ─────────────────────────────────────────────────────────────────────────

    def set_throttle(self, throttle):
        """
        Change frame throttling rate.

        Args:
            throttle: Show every Nth frame (1=all, 3=every 3rd, etc.)
        """
        self.preview_skip_target = throttle
        logger.debug(f"Preview throttle set to: every {throttle} frames")


__all__ = ['PreviewHandler']
