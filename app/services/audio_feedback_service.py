
"""
File: app/services/audio_feedback_service.py

Module Description:
    Audio feedback for user actions.
    
    Plays sound effects to confirm actions:
    - Recording start/stop beeps
    - Command confirmation sounds
    - Error alerts
    - Success notifications

Dependencies:
    - pygame: Audio playback
    - pathlib: File paths

Author: OT Video Dev Team
Date: January 30, 2026
Version: 1.0.0
"""

from typing import Tuple, Optional
from pathlib import Path

try:
    import pygame
    import pygame.mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from config.app_config import SOUNDS_DIR, AUDIO_FEEDBACK_VOLUME
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors

logger = AppLogger("AudioFeedbackService")


class AudioFeedbackService:
    """
    Audio feedback service.
    
    Plays sound effects for user feedback.
    
    Methods:
        initialize(): Initialize audio system
        play_recording_start(): Play start beep
        play_recording_stop(): Play stop beep
        play_success(): Play success sound
        play_error(): Play error sound
        set_volume(level): Set volume
    
    Example:
        >>> audio = AudioFeedbackService()
        >>> audio.initialize()
        >>> 
        >>> # Play sounds
        >>> audio.play_recording_start()
        >>> # ... recording happens ...
        >>> audio.play_recording_stop()
    """
    
    def __init__(self):
        self.initialized = False
        self.sounds = {}
        self.volume = AUDIO_FEEDBACK_VOLUME
        
        if not PYGAME_AVAILABLE:
            logger.warning("Pygame not available - audio feedback disabled")
        
        logger.info("Audio feedback service initialized")
    
    @log_errors
    def initialize(self) -> Tuple[bool, None, Optional[str]]:
        """
        Initialize audio system.
        
        Returns:
            tuple: (success, None, error_message)
        """
        if not PYGAME_AVAILABLE:
            logger.info("Audio feedback disabled (pygame not installed)")
            return True, None, None  # Not an error
        
        try:
            pygame.mixer.init()
            
            # Load sound files
            sounds_path = Path(SOUNDS_DIR)
            
            sound_files = {
                'recording_start': 'recording_start.wav',
                'recording_stop': 'recording_stop.wav',
                'command_recognized': 'command_recognized.wav',
                'error': 'error.wav',
                'notification': 'notification.wav'
            }
            
            for key, filename in sound_files.items():
                sound_path = sounds_path / filename
                if sound_path.exists():
                    self.sounds[key] = pygame.mixer.Sound(str(sound_path))
                    self.sounds[key].set_volume(self.volume)
                else:
                    logger.warning(f"Sound file not found: {filename}")
            
            self.initialized = True
            logger.info("Audio feedback initialized")
            return True, None, None
        
        except Exception as e:
            logger.error(f"Audio init error: {e}")
            return False, None, "Audio feedback not available"
    
    @log_errors
    def play_recording_start(self) -> Tuple[bool, None, Optional[str]]:
        """Play recording start sound."""
        return self._play_sound('recording_start')
    
    @log_errors
    def play_recording_stop(self) -> Tuple[bool, None, Optional[str]]:
        """Play recording stop sound."""
        return self._play_sound('recording_stop')
    
    @log_errors
    def play_success(self) -> Tuple[bool, None, Optional[str]]:
        """Play success notification."""
        return self._play_sound('notification')
    
    @log_errors
    def play_error(self) -> Tuple[bool, None, Optional[str]]:
        """Play error alert."""
        return self._play_sound('error')
    
    @log_errors
    def play_command_recognized(self) -> Tuple[bool, None, Optional[str]]:
        """Play command confirmation."""
        return self._play_sound('command_recognized')
    
    def _play_sound(self, sound_key: str) -> Tuple[bool, None, Optional[str]]:
        """Internal: Play sound by key."""
        if not self.initialized or not PYGAME_AVAILABLE:
            return True, None, None  # Silent fail
        
        try:
            if sound_key in self.sounds:
                self.sounds[sound_key].play()
                return True, None, None
            else:
                return True, None, None  # Sound not loaded
        
        except Exception as e:
            logger.error(f"Sound play error: {e}")
            return False, None, "Could not play sound"
    
    def set_volume(self, volume: float):
        """
        Set volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        
        for sound in self.sounds.values():
            sound.set_volume(self.volume)


__all__ = ['AudioFeedbackService']