"""
File: app/services/voice_command_service.py

ROBUST Voice Command Service - Error handling that never blocks main app.

DESIGN PRINCIPLES:
1. Voice is OPTIONAL - core app functions work without it
2. Errors notify user but don't crash app
3. Daemon thread - can't block main thread
4. Graceful degradation - if voice fails, everything else works
5. User always informed of voice status
6. Configurable via ENABLE_VOICE_COMMANDS flag in app_config.py

Version: 1.3.0 (Added config flag support)
Date: March 24, 2026
Changelog:
    - v1.3.0: Added ENABLE_VOICE_COMMANDS flag check to disable voice at config level
    - v1.2.0: Robust error handling
    - v1.1.0: Initial release
"""

import pyaudio
import json
import threading
import os
from pathlib import Path
from typing import Optional, Callable, Tuple

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

from app.utils.logger import AppLogger

logger = AppLogger("VoiceCommandService")


class VoiceCommandService:
    """
    Robust voice command service.
    
    ERROR HANDLING STRATEGY:
    - All operations wrapped in try-except
    - Errors logged + reported via callback
    - Background thread is daemon (can't block app exit)
    - Main app functions independent of voice service
    
    CONFIGURATION:
    - Can be completely disabled via ENABLE_VOICE_COMMANDS = False in config
    - When disabled, all methods return gracefully without errors
    """
    
    def __init__(self):
        """Initialize voice service with safe defaults."""
        # Initialize default attributes (safe defaults)
        self.model = None
        self.recognizer = None
        self.is_listening = False
        self.callback = None
        
        # Audio resources
        self.audio = None
        self.stream = None
        self.thread = None
        
        # Configuration
        self.sample_rate = 16000
        self.chunk_size = 4000
        
        # Wake word system
        self.wake_word_mode = True
        self.wake_words = ["hey computer", "computer", "okay computer"]
        
        # Error tracking
        self.initialization_error = None
        self.last_error = None
        
        # ====================================================================
        # CHECK CONFIGURATION FLAG - Voice can be disabled at config level
        # ====================================================================
        try:
            from config.app_config import ENABLE_VOICE_COMMANDS
            if not ENABLE_VOICE_COMMANDS:
                self.initialization_error = "Voice commands disabled by configuration"
                logger.info("Voice commands disabled by ENABLE_VOICE_COMMANDS flag")
                # Service remains in disabled state - all methods will return False
                return
        except ImportError:
            # Config module not accessible - proceed with normal initialization
            # This allows voice service to work even if config import fails
            logger.debug("Could not import ENABLE_VOICE_COMMANDS from config")
        except Exception as e:
            logger.warning(f"Error checking voice config flag: {e}")
        
        # ====================================================================
        # NORMAL INITIALIZATION (only if voice is enabled)
        # ====================================================================
        
        # Check if Vosk library is available
        if not VOSK_AVAILABLE:
            self.initialization_error = "Vosk not installed"
            logger.warning("⚠ Vosk not installed - voice commands disabled")
            return
        
        # Load the Vosk model
        try:
            self._load_model()
        except Exception as e:
            self.initialization_error = f"Model load failed: {e}"
            logger.error(f"✗ Voice initialization failed: {e}")
    
    def _load_model(self):
        """Load Vosk model with multiple fallback paths."""
        home = str(Path.home())
        
        possible_paths = [
            os.path.join(home, "vosk-models", "vosk-model-small-en-us-0.15"),
            os.path.join(home, "vosk", "vosk-model-small-en-us-0.15"),
            os.path.join(os.getcwd(), "vosk-models", "vosk-model-small-en-us-0.15"),
            os.path.join(os.getcwd(), "vosk-model-small-en-us-0.15"),
        ]
        
        for model_path in possible_paths:
            if os.path.exists(model_path):
                try:
                    logger.info(f"Loading Vosk model: {model_path}")
                    self.model = Model(model_path)
                    self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
                    self.recognizer.SetWords(True)
                    logger.info("✓ Voice command service initialized")
                    logger.info(f"  Model: {os.path.basename(model_path)}")
                    return
                except Exception as e:
                    logger.error(f"✗ Failed to load {model_path}: {e}")
                    continue
        
        self.initialization_error = "Vosk model not found"
        logger.error("✗ Vosk model not found in any location")
    
    def is_available(self) -> bool:
        """
        Check if voice service is ready.
        
        Returns:
            bool: True if voice is enabled AND model is loaded, False otherwise
        """
        return (
            VOSK_AVAILABLE and 
            self.model is not None and 
            self.recognizer is not None and
            self.initialization_error is None
        )
    
    def is_enabled(self) -> bool:
        """
        Check if voice service is enabled at config level.
        
        Returns:
            bool: True if voice is enabled in config, False if disabled
        """
        try:
            from config.app_config import ENABLE_VOICE_COMMANDS
            return ENABLE_VOICE_COMMANDS
        except:
            # If config not accessible, assume enabled
            return True
    
    def set_command_callback(self, callback: Callable[[str], None]):
        """
        Set callback for voice events.
        
        Callback receives:
        - "wake_word_detected" - User said wake word
        - "start_recording" - Command recognized
        - "stop_recording" - Command recognized
        - "go_to_library" - Command recognized
        - "go_to_settings" - Command recognized
        - "cancel" - Command recognized
        - "voice_error:message" - Error occurred
        
        Args:
            callback: Function to call when voice events occur
        """
        if not self.is_available():
            logger.debug("Voice not available - callback not set")
            return
        
        self.callback = callback
        logger.debug("Command callback set")
    
    def start_listening(self) -> Tuple[bool, Optional[str]]:
        """
        Start voice recognition.
        
        ROBUST: Returns False if fails, but doesn't crash app.
        
        Returns:
            (success: bool, error_message: str or None)
        """
        # Check if voice is disabled at config level
        if not self.is_enabled():
            return True, None  # Silent success - voice intentionally off
        
        # Check availability
        if not self.is_available():
            error = self.initialization_error or "Voice service unavailable"
            logger.error(f"✗ Cannot start: {error}")
            return False, error
        
        # Already listening
        if self.is_listening:
            logger.debug("Already listening")
            return True, None
        
        try:
            # Initialize PyAudio (may fail if no microphone)
            try:
                self.audio = pyaudio.PyAudio()
                device_count = self.audio.get_device_count()
                logger.info(f"Found {device_count} audio device(s)")
            except Exception as e:
                raise Exception(f"No audio devices: {e}")
            
            # Open microphone stream (may fail if mic busy/unplugged)
            try:
                self.stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk_size
                )
                logger.info("✓ Audio stream opened")
            except Exception as e:
                raise Exception(f"Cannot open microphone: {e}")
            
            # Start recognition thread (daemon - won't block exit)
            self.is_listening = True
            self.thread = threading.Thread(
                target=self._recognition_loop,
                daemon=True,  # ← CRITICAL: Won't block app exit
                name="VoiceRecognition"
            )
            self.thread.start()
            
            logger.info("🎤 Voice listening started")
            logger.info("   Say 'Hey Computer' to activate")
            return True, None
        
        except Exception as e:
            # Cleanup on failure
            self._cleanup()
            error_msg = str(e)
            self.last_error = error_msg
            logger.error(f"✗ Failed to start: {error_msg}")
            return False, error_msg
    
    def stop_listening(self):
        """
        Stop voice recognition.
        
        ROBUST: Always succeeds, cleans up resources.
        """
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        # Wait for thread (with timeout - won't hang)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            if self.thread.is_alive():
                logger.warning("⚠ Thread didn't stop gracefully (will exit anyway)")
        
        # Cleanup resources
        self._cleanup()
        
        logger.info("✓ Voice listening stopped")
    
    def _cleanup(self):
        """
        Clean up audio resources.
        
        ROBUST: Never throws exceptions, always succeeds.
        """
        # Close stream
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.debug(f"Stream cleanup warning: {e}")
            finally:
                self.stream = None
        
        # Terminate PyAudio
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.debug(f"PyAudio cleanup warning: {e}")
            finally:
                self.audio = None
    
    def _recognition_loop(self):
        """
        Main recognition loop with comprehensive error handling.
        
        ROBUST FEATURES:
        - Wrapped in try-except
        - Notifies user of errors via callback
        - Exits gracefully on error
        - Won't crash main app (daemon thread)
        """
        logger.debug("Recognition loop started")
        error_count = 0
        max_errors = 5  # Stop after 5 consecutive errors
        
        while self.is_listening:
            try:
                # Read audio chunk
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Feed to Vosk
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower().strip()
                    
                    if text:
                        logger.debug(f"Recognized: {text}")
                        self._process_text(text)
                        error_count = 0  # Reset error count on success
            
            except Exception as e:
                error_count += 1
                logger.error(f"✗ Recognition error #{error_count}: {e}")
                
                # Stop after too many errors
                if error_count >= max_errors:
                    logger.error(f"✗ Too many errors ({max_errors}), stopping")
                    self.is_listening = False
                    
                    # Notify user via callback
                    if self.callback:
                        try:
                            self.callback(f"voice_error:{e}")
                        except:
                            pass  # Don't let callback error crash thread
                    
                    break
        
        logger.debug("Recognition loop ended")
        
        # Final cleanup
        self._cleanup()
    
    def _process_text(self, text: str):
        """
        Process recognized text.
        
        ROBUST: Callback errors won't crash recognition.
        
        Args:
            text: Recognized text string
        """
        try:
            # Check wake word
            if self.wake_word_mode:
                if self._is_wake_word(text):
                    logger.info(f"Wake word: {text}")
                    self.wake_word_mode = False
                    if self.callback:
                        self.callback("wake_word_detected")
                    return
            
            # Extract command
            command = self._extract_command(text)
            if command:
                logger.info(f"Command: {command}")
                self.wake_word_mode = True
                
                if self.callback:
                    self.callback(command)
        
        except Exception as e:
            logger.error(f"✗ Text processing error: {e}")
            # Continue listening despite error
    
    def _is_wake_word(self, text: str) -> bool:
        """
        Check if text contains wake word.
        
        Args:
            text: Recognized text string
            
        Returns:
            bool: True if wake word detected
        """
        return any(word in text for word in self.wake_words)
    
    def _extract_command(self, text: str) -> Optional[str]:
        """
        Extract command from recognized text.
        
        Args:
            text: Recognized text string
            
        Returns:
            str or None: Command string if recognized, None otherwise
        """
        # Start recording
        if any(p in text for p in ["start recording", "begin recording", "record"]):
            return "start_recording"
        
        # Stop recording
        if any(p in text for p in ["stop recording", "end recording", "stop"]):
            return "stop_recording"
        
        # Go to library
        if any(p in text for p in ["go to library", "show library", "library"]):
            return "go_to_library"
        
        # Go to settings
        if any(p in text for p in ["go to settings", "settings"]):
            return "go_to_settings"
        
        # Cancel
        if any(p in text for p in ["cancel", "never mind"]):
            return "cancel"
        
        return None
    
    def __del__(self):
        """Cleanup on deletion (safe)."""
        try:
            self.stop_listening()
        except:
            pass  # Ignore errors during cleanup


__all__ = ['VoiceCommandService']