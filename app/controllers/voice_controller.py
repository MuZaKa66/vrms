
"""
File: app/controllers/voice_controller.py

Module Description:
    Voice command controller.
    
    Handles voice recognition and command execution:
    - Start/stop listening
    - Recognize commands
    - Execute commands
    - Audio feedback

Author: OT Video Dev Team
Date: January 30, 2026
"""

from typing import Tuple, Optional, Dict, Callable
from app.services.voice_recognition_service import VoiceRecognitionService
from app.services.audio_feedback_service import AudioFeedbackService
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors

logger = AppLogger("VoiceController")


class VoiceController:
    """
    Voice command controller.
    
    Methods:
        initialize(): Initialize voice recognition
        start_listening(): Begin listening
        stop_listening(): Stop listening
        process_command(): Process recognized text
        register_command(phrase, callback): Register command
    
    Example:
        >>> controller = VoiceController()
        >>> controller.initialize()
        >>> 
        >>> # Register commands
        >>> controller.register_command("start recording", start_recording_func)
        >>> controller.register_command("stop recording", stop_recording_func)
        >>> 
        >>> # Start listening
        >>> controller.start_listening()
        >>> 
        >>> # Process commands
        >>> success, command, error = controller.process_command()
        >>> if command:
        ...     print(f"Executed: {command}")
    """
    
    def __init__(self):
        self.voice = VoiceRecognitionService()
        self.audio = AudioFeedbackService()
        self.commands = {}  # phrase -> callback mapping
        self.is_listening = False
        logger.info("Voice controller initialized")
    
    @log_errors
    def initialize(self) -> Tuple[bool, None, Optional[str]]:
        """
        Initialize voice recognition.
        
        Returns:
            tuple: (success, None, error_message)
        """
        # Initialize voice
        success, _, error = self.voice.initialize()
        if not success:
            return False, None, error
        
        # Initialize audio
        self.audio.initialize()
        
        # Register default commands
        self._register_default_commands()
        
        logger.info("Voice recognition ready")
        return True, None, None
    
    @log_errors
    def start_listening(self) -> Tuple[bool, None, Optional[str]]:
        """Start listening for commands."""
        success, _, error = self.voice.start_listening()
        if success:
            self.is_listening = True
        return success, None, error
    
    def stop_listening(self):
        """Stop listening."""
        self.voice.stop_listening()
        self.is_listening = False
    
    @log_errors
    def process_command(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process voice input.
        
        Returns:
            tuple: (success, command_executed, error_message)
        """
        if not self.is_listening:
            return False, None, "Not listening"
        
        try:
            # Recognize speech
            success, text, error = self.voice.recognize()
            
            if not success or not text:
                return True, None, None  # No speech yet
            
            # Match command
            text_lower = text.lower()
            
            for phrase, callback in self.commands.items():
                if phrase.lower() in text_lower:
                    # Execute command
                    logger.info(f"Voice command: {phrase}")
                    self.audio.play_command_recognized()
                    callback()
                    return True, phrase, None
            
            return True, None, None  # No matching command
            
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            return False, None, "Voice command failed"
    
    def register_command(self, phrase: str, callback: Callable):
        """
        Register voice command.
        
        Args:
            phrase: Command phrase (e.g., "start recording")
            callback: Function to call when command recognized
        """
        self.commands[phrase] = callback
        logger.debug(f"Registered command: {phrase}")
    
    def _register_default_commands(self):
        """Register default commands (placeholders)."""
        # These will be connected to actual functions by the GUI
        self.commands = {
            "start recording": lambda: logger.info("Start recording command"),
            "stop recording": lambda: logger.info("Stop recording command"),
            "pause recording": lambda: logger.info("Pause recording command"),
            "save recording": lambda: logger.info("Save recording command"),
            "cancel recording": lambda: logger.info("Cancel recording command"),
        }


__all__ = ['VoiceController']