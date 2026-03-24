"""
File: app/services/voice_command_service.py

Voice command service using Vosk for offline speech recognition.
"""

import pyaudio
import json
import threading
import queue
from pathlib import Path
from typing import Optional, Callable, Tuple

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

from config.app_config import VOSK_MODEL_PATH
from app.utils.logger import AppLogger

logger = AppLogger("VoiceCommandService")


class VoiceCommandService:
    """Voice command recognition service."""
    
    def __init__(self):
        """Initialize voice command service."""
        self.is_listening = False
        self.recognition_thread = None
        self.command_callback = None
        
        self.sample_rate = 16000
        self.chunk_size = 4000
        
        self.audio = None
        self.stream = None
        
        self.model = None
        self.recognizer = None
        
        self.wake_word_mode = True
        self.wake_words = ["hey computer", "computer", "okay computer"]
        
        self.command_queue = queue.Queue()
        
        if not VOSK_AVAILABLE:
            logger.warning("Vosk not installed - voice commands disabled")
            return
        
        if not self._load_model():
            logger.error("Failed to load Vosk model - voice commands disabled")
            return
        
        logger.info("Voice command service initialized")
    
    def _load_model(self) -> bool:
        """Load Vosk model."""
        if not Path(VOSK_MODEL_PATH).exists():
            logger.error(f"Vosk model not found: {VOSK_MODEL_PATH}")
            return False
        
        try:
            logger.info(f"Loading Vosk model from: {VOSK_MODEL_PATH}")
            self.model = Model(VOSK_MODEL_PATH)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            logger.info("Vosk model loaded successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            return False
    
    def set_command_callback(self, callback: Callable[[str], None]):
        """Set callback for recognized commands."""
        self.command_callback = callback
        logger.debug("Command callback set")
    
    def is_available(self) -> bool:
        """Check if voice commands are available."""
        return VOSK_AVAILABLE and self.model is not None
    
    def start_listening(self) -> Tuple[bool, Optional[str]]:
        """Start continuous voice recognition."""
        if not self.is_available():
            return False, "Voice recognition not available"
        
        if self.is_listening:
            return True, None
        
        try:
            self.audio = pyaudio.PyAudio()
            
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_listening = True
            self.recognition_thread = threading.Thread(
                target=self._recognition_loop,
                daemon=True,
                name="VoiceRecognition"
            )
            self.recognition_thread.start()
            
            logger.info("Voice recognition started")
            return True, None
        
        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            self._cleanup_audio()
            return False, str(e)
    
    def stop_listening(self):
        """Stop voice recognition."""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2.0)
        
        self._cleanup_audio()
        
        logger.info("Voice recognition stopped")
    
    def _cleanup_audio(self):
        """Clean up audio stream."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
            self.audio = None
    
    def _recognition_loop(self):
        """Main recognition loop."""
        logger.debug("Recognition loop started")
        
        while self.is_listening:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower().strip()
                    
                    if text:
                        logger.debug(f"Recognized: {text}")
                        self._process_text(text)
            
            except Exception as e:
                logger.error(f"Recognition loop error: {e}")
                break
        
        logger.debug("Recognition loop ended")
    
    def _process_text(self, text: str):
        """Process recognized text."""
        if self.wake_word_mode:
            if self._is_wake_word(text):
                logger.info(f"Wake word detected: {text}")
                self.wake_word_mode = False
                if self.command_callback:
                    self.command_callback("wake_word_detected")
                return
        
        command = self._extract_command(text)
        if command:
            logger.info(f"Command recognized: {command}")
            self.wake_word_mode = True
            
            if self.command_callback:
                self.command_callback(command)
    
    def _extract_command(self, text: str) -> Optional[str]:
        """Extract command from text."""
        if any(phrase in text for phrase in ["start recording", "begin recording", "record"]):
            return "start_recording"
        
        if any(phrase in text for phrase in ["stop recording", "end recording", "stop"]):
            return "stop_recording"
        
        if any(phrase in text for phrase in ["go to library", "show library", "show recordings", "library"]):
            return "go_to_library"
        
        if any(phrase in text for phrase in ["go to settings", "open settings", "settings"]):
            return "go_to_settings"
        
        if any(phrase in text for phrase in ["delete last recording", "remove last recording"]):
            return "delete_last"
        
        if any(phrase in text for phrase in ["cancel", "never mind", "nevermind"]):
            return "cancel"
        
        logger.debug(f"No command found in: {text}")
        return None
    
    def _is_wake_word(self, text: str) -> bool:
        """Check if text contains wake word."""
        return any(wake_word in text for wake_word in self.wake_words)
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop_listening()


__all__ = ['VoiceCommandService']