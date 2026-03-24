"""
File: app/services/voice_recognition_service.py

Module Description:
    Offline voice recognition using Vosk.
    
    Hands-free operation for doctors:
    - Offline recognition (no network needed)
    - Real-time speech-to-text
    - Confidence scoring
    - Command detection
    - Professional error handling

Dependencies:
    - vosk: Offline speech recognition
    - pyaudio: Microphone input
    - wave: Audio processing

Author: OT Video Dev Team
Date: January 30, 2026
Version: 1.0.0
"""

import json
from typing import Tuple, Optional, Dict
from pathlib import Path

try:
    from vosk import Model, KaldiRecognizer
    import pyaudio
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

from config.app_config import (
    VOSK_MODEL_PATH,
    AUDIO_RATE,
    AUDIO_CHUNK_SIZE,
    VOICE_CONFIDENCE_THRESHOLD
)
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors

logger = AppLogger("VoiceRecognitionService")

"""
File: app/services/voice_recognition_service.py

Module Description:
    Voice recognition service for hands-free operation.
    
    Offline speech-to-text using Vosk model.
    Provides methods to start/stop listening and recognize commands.

Dependencies:
    - vosk: Speech recognition library
    - pyaudio: Microphone access
    - json: Parse recognition results

Author: OT Video Dev Team
Date: March 24, 2026
Version: 1.1.0
Changelog:
    - v1.1.0: Added ENABLE_VOICE_COMMANDS flag check for conditional initialization
    - v1.0.0: Initial release
"""

import json
from pathlib import Path
from typing import Tuple, Optional

# Import audio libraries with fallback
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    Model = None
    KaldiRecognizer = None

from config.app_config import (
    VOSK_MODEL_PATH,
    AUDIO_RATE,
    AUDIO_CHUNK_SIZE,
    ENABLE_VOICE_COMMANDS
)
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors

logger = AppLogger("VoiceRecognitionService")


class VoiceRecognitionService:
    """
    Voice recognition service.
    
    Offline speech-to-text for hands-free operation.
    Can be disabled via ENABLE_VOICE_COMMANDS config flag.
    
    Methods:
        initialize(): Load Vosk model (skips if disabled)
        start_listening(): Begin listening
        stop_listening(): Stop listening
        recognize(): Get recognized text
    
    Example:
        >>> voice = VoiceRecognitionService()
        >>> success, _, error = voice.initialize()
        >>> 
        >>> if success:
        >>>     # Start listening
        >>>     success, _, error = voice.start_listening()
        >>>     
        >>>     # Recognize speech
        >>>     success, text, error = voice.recognize()
        >>>     if success and text:
        >>>         print(f"Heard: {text}")
    """
    
    def __init__(self):
        """
        Initialize voice recognition service.
        
        Checks ENABLE_VOICE_COMMANDS flag. If disabled, service remains inactive.
        All methods will return early when voice commands are disabled.
        """
        self.model = None
        self.recognizer = None
        self.audio = None
        self.stream = None
        self.is_listening = False
        self._disabled = False
        
        # Check if voice commands are enabled in configuration
        if not ENABLE_VOICE_COMMANDS:
            self._disabled = True
            logger.info("Voice commands disabled by ENABLE_VOICE_COMMANDS flag")
            return
        
        if not VOSK_AVAILABLE:
            self._disabled = True
            logger.warning("Vosk library not available - voice commands disabled")
            return
        
        if not PYAUDIO_AVAILABLE:
            self._disabled = True
            logger.warning("PyAudio not available - microphone access disabled")
            return
        
        logger.info("Voice recognition service initialized (enabled)")
    
    def _check_enabled(self) -> bool:
        """
        Check if voice recognition is enabled.
        
        Returns:
            bool: True if enabled and ready, False otherwise
        """
        if self._disabled:
            return False
        if not VOSK_AVAILABLE or not PYAUDIO_AVAILABLE:
            return False
        return True
    
    @log_errors
    def initialize(self) -> Tuple[bool, None, Optional[str]]:
        """
        Initialize voice recognition model.
        
        If voice commands are disabled via ENABLE_VOICE_COMMANDS flag,
        this method returns success without loading the model.
        
        Returns:
            tuple: (success, None, error_message)
        """
        # Skip if voice commands are disabled
        if not self._check_enabled():
            if self._disabled:
                logger.debug("Voice commands disabled - skipping initialization")
            else:
                logger.warning("Voice libraries not available - cannot initialize")
            return True, None, None
        
        try:
            model_path = Path(VOSK_MODEL_PATH)
            
            if not model_path.exists():
                return False, None, (
                    "Voice recognition model not found. "
                    f"Expected at: {model_path}\n"
                    "Please download model from: "
                    "https://alphacephei.com/vosk/models"
                )
            
            # Load model
            logger.info(f"Loading voice model from: {model_path}")
            self.model = Model(str(model_path))
            
            # Create recognizer
            self.recognizer = KaldiRecognizer(self.model, AUDIO_RATE)
            
            logger.info("Voice model loaded successfully")
            return True, None, None
        
        except Exception as e:
            logger.error(f"Voice model initialization error: {e}")
            return False, None, f"Could not load voice recognition model: {e}"
    
    @log_errors
    def start_listening(self) -> Tuple[bool, None, Optional[str]]:
        """
        Start listening to microphone.
        
        Returns:
            tuple: (success, None, error_message)
        """
        # Skip if voice commands are disabled
        if not self._check_enabled():
            return True, None, None
        
        if not self.model or not self.recognizer:
            return False, None, "Voice model not initialized"
        
        if self.is_listening:
            return True, None, None
        
        try:
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Open microphone stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=AUDIO_RATE,
                input=True,
                frames_per_buffer=AUDIO_CHUNK_SIZE
            )
            
            self.is_listening = True
            logger.info("Microphone listening started")
            return True, None, None
        
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            return False, None, (
                "Cannot access microphone. "
                "Please check USB connection or audio input device."
            )
    
    @log_errors
    def recognize(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Recognize speech from microphone.
        
        Returns:
            tuple: (success, recognized_text, error_message)
        """
        # Skip if voice commands are disabled
        if not self._check_enabled():
            return True, None, None
        
        if not self.is_listening or not self.stream:
            return False, None, "Not listening"
        
        try:
            # Read audio data
            data = self.stream.read(AUDIO_CHUNK_SIZE, exception_on_overflow=False)
            
            # Process with recognizer
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '')
                
                if text:
                    logger.debug(f"Recognized: {text}")
                    return True, text, None
            
            return True, None, None  # No speech yet or partial result
        
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return False, None, f"Speech recognition failed: {e}"
    
    def stop_listening(self):
        """
        Stop listening and release microphone resources.
        """
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing stream: {e}")
            self.stream = None
        
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.error(f"Error terminating audio: {e}")
            self.audio = None
        
        self.is_listening = False
        logger.debug("Microphone stopped")
    
    def is_available(self) -> bool:
        """
        Check if voice recognition is available and enabled.
        
        Returns:
            bool: True if voice commands are enabled and libraries are available
        """
        return self._check_enabled() and self.model is not None
    
    def __del__(self):
        """Clean up resources on deletion."""
        self.stop_listening()


__all__ = ['VoiceRecognitionService']


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