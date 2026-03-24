"""
File: app/services/thumbnail_service.py

Module Description:
    Video thumbnail generation service.
    
    Creates preview images from video files for library display.

Dependencies:
    - cv2 (OpenCV): Frame extraction
    - PIL (Pillow): Image processing

Author: OT Video Dev Team
Date: January 30, 2026
Version: 1.0.0
"""

from typing import Tuple, Optional
from pathlib import Path
import cv2
from PIL import Image

from config.app_config import THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, THUMBNAIL_QUALITY
from app.utils.logger import AppLogger
from app.utils.file_utils import ensure_directory
from app.utils.decorators import log_errors

logger = AppLogger("ThumbnailService")


class ThumbnailService:
    """
    Thumbnail generation service.
    
    Methods:
        generate_thumbnail(video_path, output_path): Create thumbnail
        extract_frame(video_path, time_offset): Extract frame at time
    
    Example:
        >>> thumb = ThumbnailService()
        >>> success, path, error = thumb.generate_thumbnail(
        ...     "video.mp4",
        ...     "thumb.jpg"
        ... )
    """
    
    @log_errors
    def generate_thumbnail(self, video_path: str, output_path: str,
                          time_offset_seconds: int = 5) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate thumbnail from video.
        
        Args:
            video_path: Path to video file
            output_path: Path for thumbnail output
            time_offset_seconds: Time offset for frame extraction
        
        Returns:
            tuple: (success, thumbnail_path, error_message)
        """
        try:
            video_path = Path(video_path)
            output_path = Path(output_path)
            
            if not video_path.exists():
                return False, None, "Video file not found"
            
            # Ensure output directory exists
            ensure_directory(output_path.parent)
            
            # Open video
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                return False, None, "Cannot open video file"
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate frame number
            frame_number = min(int(fps * time_offset_seconds), total_frames - 1)
            
            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, None, "Could not extract frame"
            
            # Resize frame
            frame_resized = cv2.resize(frame, (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Save as JPEG
            img = Image.fromarray(frame_rgb)
            img.save(str(output_path), 'JPEG', quality=THUMBNAIL_QUALITY)
            
            logger.info(f"Thumbnail created: {output_path.name}")
            return True, str(output_path), None
        
        except Exception as e:
            logger.error(f"Thumbnail error: {e}")
            return False, None, "Could not create thumbnail"


__all__ = ['ThumbnailService']