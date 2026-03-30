"""
File: app/gui/main_window.py

ROBUST Main Window - Voice is optional, core features always work.

DESIGN PRINCIPLES:
1. Recording/Library/Playback work WITHOUT voice
2. Voice errors show user-friendly messages
3. Button state always syncs with actual voice state
4. No voice errors can crash the app
5. User always informed of voice status

Version: 3.1.0 (Robust error handling)
Date: February 13, 2026
"""



from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from config.app_config import WINDOW_WIDTH, WINDOW_HEIGHT
from app.gui.recording import RecordingScreen
from app.gui.library_screen import LibraryScreen
from app.gui.playback_screen import PlaybackScreen
from app.gui.settings_screen import SettingsScreen
from app.services.system_monitor_service import SystemMonitorService
from app.utils.logger import AppLogger
from app.utils.constants import RecordingState
from app.gui.dialogs import CloseConfirmDialog
# Voice imports (OPTIONAL - app works without)
try:
    from app.services.voice_command_service import VoiceCommandService
    from app.gui.widgets.voice_indicator_widget import VoiceIndicatorWidget
    VOICE_AVAILABLE = False
except ImportError as e:
    VOICE_AVAILABLE = False

logger = AppLogger("MainWindow")


class MainWindow(QMainWindow):
    """
    Main window with robust voice integration.
    
    VOICE ERROR HANDLING:
    - Voice errors show user-friendly dialogs
    - Button state syncs with actual voice state
    - Core features (recording/library) unaffected by voice errors
    - Voice can be restarted after error
    """
    
    def __init__(self):
        super().__init__()
        self.system_monitor = SystemMonitorService()
    # Voice (optional)
        self.voice_service = None
        self.voice_indicator = None
        self.voice_enabled = False  # Track actual voice state
        
        self.init_ui()
        
        # Initialize voice if available
        self.init_voice()
        
        self.start_system_monitoring()
        
        #self.showMaximized() # t test picking resolution from cofig file
        #self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.showFullScreen()
        #self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        print(f"Window set to: {self.width()} x {self.height()}")
        
        logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize UI (voice-independent)."""
        self.setWindowTitle("OT Video Management System")
        self.setMinimumSize(800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar
        self.top_bar = self.create_top_status_bar()
        main_layout.addWidget(self.top_bar)
        
        # Screen container
        self.screens = QStackedWidget()
        main_layout.addWidget(self.screens, stretch=1)
        
        # Create screens (independent of voice)
        self.recording_screen = RecordingScreen()
        self.library_screen = LibraryScreen(self)
        self.playback_screen = PlaybackScreen()
        self.settings_screen = SettingsScreen()
        
        # Add to stack
        self.screens.addWidget(self.recording_screen)
        self.screens.addWidget(self.library_screen)
        self.screens.addWidget(self.playback_screen)
        self.screens.addWidget(self.settings_screen)
        
        # Connect playback back button
        self.playback_screen.back_clicked.connect(self.show_library_screen)
        
        # Navigation bar
        self.nav_bar = self.create_bottom_navigation_bar()
        main_layout.addWidget(self.nav_bar)
        
        # Show recording screen
        self.show_recording_screen()
    
    def create_top_status_bar(self):
        """Create top bar with optional voice button."""
        bar = QWidget()
        bar.setFixedHeight(50)
        bar.setStyleSheet("QWidget { background-color: #2c3e50; color: white; }")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("OT Video Management System")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Voice button (if available)
        if VOICE_AVAILABLE:
            self.voice_btn = QPushButton("🎤")
            self.voice_btn.setFixedSize(40, 40)
            self.voice_btn.setFont(QFont("Arial", 20))
            self.voice_btn.setToolTip("Voice Commands (Click to toggle)")
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 20px;
                }
                QPushButton:checked {
                    background-color: #3498db;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            self.voice_btn.setCheckable(True)
            self.voice_btn.clicked.connect(self.toggle_voice)
            layout.addWidget(self.voice_btn)
            
            sep = QLabel("|")
            sep.setStyleSheet("color: #7f8c8d;")
            layout.addWidget(sep)
        
        # Storage
        self.storage_label = QLabel("Storage: --")
        self.storage_label.setFont(QFont("Arial", 12))
        self.storage_label.setStyleSheet("color: white;")
        layout.addWidget(self.storage_label)
        
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(sep1)
        
        # Temperature
        self.temp_label = QLabel("Temp: --°C")
        self.temp_label.setFont(QFont("Arial", 12))
        self.temp_label.setStyleSheet("color: white;")
        layout.addWidget(self.temp_label)
        
        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(sep2)
        
        # Exit
        exit_btn = QPushButton("✕")
        exit_btn.setFixedSize(40, 40)
        exit_btn.setFont(QFont("Arial", 20, QFont.Bold))
        exit_btn.setToolTip("Close Application")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
        
        return bar
    
    def create_bottom_navigation_bar(self):
        """Create navigation bar (voice-independent)."""
        bar = QWidget()
        bar.setFixedHeight(80)
        bar.setStyleSheet("background-color: #34495e;")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Record
        btn_rec = self.create_nav_button("🎥", "Record")
        btn_rec.clicked.connect(self.show_recording_screen)
        layout.addWidget(btn_rec)
        
        # Library
        btn_lib = self.create_nav_button("📚", "Library")
        btn_lib.clicked.connect(self.show_library_screen)
        layout.addWidget(btn_lib)
        
        # Settings
        btn_set = self.create_nav_button("⚙️", "Settings")
        btn_set.clicked.connect(self.show_settings_screen)
        layout.addWidget(btn_set)
        
        return bar
    
    def create_nav_button(self, icon, text):
        """Create navigation button."""
        btn = QPushButton(f"{icon}\n{text}")
        btn.setMinimumSize(200, 60)
        btn.setFont(QFont("Arial", 14, QFont.Bold))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        return btn
    
    def init_voice(self):
        """
        Initialize voice commands (OPTIONAL).
        
        ROBUST: Initialization errors won't crash app.
        """
        if not VOICE_AVAILABLE:
            logger.info("Voice commands not available (imports failed)")
            return
        
        try:
            # Create service
            self.voice_service = VoiceCommandService()
            
            if not self.voice_service.is_available():
                logger.warning("Voice service created but not available")
                return
            
            # Set callback
            self.voice_service.set_command_callback(self.handle_voice_command)
            
            # Create indicator widget
            self.voice_indicator = VoiceIndicatorWidget(self)
            self.voice_indicator.move(
                self.width() - 140,
                self.height() - 140
            )
            self.voice_indicator.hide()
            
            logger.info("Voice commands initialized (ready)")
        
        except Exception as e:
            logger.error(f"Voice initialization error: {e}")
            self.voice_service = None
            # App continues without voice
    
    def toggle_voice(self):
        """
        Toggle voice listening with robust error handling.
        
        ROBUST: Voice errors show user dialog but don't crash app.
        """
        if not self.voice_service:
            QMessageBox.information(
                self, 
                "Voice Unavailable", 
                "Voice commands require:\n\n"
                "1. Vosk package: pip install vosk\n"
                "2. Vosk model in ~/vosk-models/\n"
                "3. Working microphone\n\n"
                "App works fine without voice!"
            )
            self.voice_btn.setChecked(False)
            return
        
        if self.voice_btn.isChecked():
            # START voice
            success, error = self.voice_service.start_listening()
            
            if success:
                self.voice_enabled = True
                self.voice_indicator.show()
                self.voice_indicator.set_idle()
                logger.info("✓ Voice listening started")
            else:
                # Show user-friendly error
                self.voice_btn.setChecked(False)
                self.voice_enabled = False
                
                QMessageBox.warning(
                    self,
                    "Voice Error",
                    f"Cannot start voice commands:\n\n{error}\n\n"
                    "Possible causes:\n"
                    "• No microphone connected\n"
                    "• Microphone in use by another app\n"
                    "• Permission denied\n\n"
                    "Recording and other features work fine without voice!"
                )
                logger.error(f"✗ Voice start failed: {error}")
        else:
            # STOP voice
            self.voice_service.stop_listening()
            self.voice_enabled = False
            self.voice_indicator.hide()
            logger.info("✓ Voice listening stopped")
    
    def handle_voice_command(self, command: str):
        """
        Handle voice commands and errors.
        
        ROBUST: Command execution errors won't crash voice system.
        """
        logger.info(f"Voice command: {command}")
        
        # ===================================================================
        # VOICE ERROR HANDLING
        # ===================================================================
        if command.startswith("voice_error:"):
            error_msg = command.split(":", 1)[1]
            
            # Update UI
            if self.voice_indicator:
                self.voice_indicator.set_error("Error")
            
            if self.voice_btn:
                self.voice_btn.setChecked(False)
            
            self.voice_enabled = False
            
            # Show error to user
            QMessageBox.warning(
                self,
                "Voice Recognition Error",
                f"Voice recognition stopped:\n\n{error_msg}\n\n"
                "Click the microphone button to restart.\n\n"
                "All other features continue working!"
            )
            
            logger.error(f"✗ Voice error: {error_msg}")
            return
        
        # ===================================================================
        # WAKE WORD
        # ===================================================================
        if command == "wake_word_detected":
            if self.voice_indicator:
                self.voice_indicator.set_listening()
            return
        
        # Show recognized
        if self.voice_indicator:
            self.voice_indicator.set_recognized()
        
        # ===================================================================
        # EXECUTE COMMANDS (with error protection)
        # ===================================================================
        try:
            if command == "start_recording":
                self.show_recording_screen()
                self.recording_screen.start_recording()
            
            elif command == "stop_recording":
                if self.recording_screen.controller.state == RecordingState.RECORDING:
                    self.recording_screen.stop_recording()
            
            elif command == "go_to_library":
                self.show_library_screen()
            
            elif command == "go_to_settings":
                self.show_settings_screen()
            
            elif command == "cancel":
                pass  # Just acknowledge
            
            else:
                logger.warning(f"Unknown command: {command}")
        
        except Exception as e:
            # Command execution failed - log but don't crash voice
            logger.error(f"✗ Command execution error: {e}")
            if self.voice_indicator:
                self.voice_indicator.set_error("Error")
    
    def show_recording_screen(self):
        """Switch to recording (voice-independent)."""
        self.screens.setCurrentWidget(self.recording_screen)
    
    def show_library_screen(self):
        """Switch to library (voice-independent)."""
        self.library_screen.refresh()
        self.screens.setCurrentWidget(self.library_screen)
    
    def show_settings_screen(self):
        """Switch to settings (voice-independent)."""
        self.screens.setCurrentWidget(self.settings_screen)
    
    def start_system_monitoring(self):
        """Start system monitoring (voice-independent)."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_system_status)
        self.monitor_timer.start(5000)
        self.update_system_status()
    
    def update_system_status(self):
        """Update system status (voice-independent)."""
        success, health, error = self.system_monitor.get_system_health()
        
        if success:
            storage_gb = health.get('storage_gb', 0)
            self.storage_label.setText(f"Storage: {storage_gb:.1f} GB free")
            
            status = health.get('status', 'healthy')
            if status == 'critical':
                self.storage_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            elif status == 'warning':
                self.storage_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            else:
                self.storage_label.setStyleSheet("color: #27ae60;")
            
            temp = health.get('temperature', 0)
            if temp > 0:
                self.temp_label.setText(f"Temp: {temp:.1f}°C")
                if temp > 75:
                    self.temp_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                elif temp > 65:
                    self.temp_label.setStyleSheet("color: #f39c12;")
                else:
                    self.temp_label.setStyleSheet("color: white;")
    
    def resizeEvent(self, event):
        """Keep voice indicator in corner."""
        super().resizeEvent(event)
        if self.voice_indicator:
            self.voice_indicator.move(
                self.width() - 140,
                self.height() - 140
            )
    
    def closeEvent(self, event):
        """
        Handle window close event (red X button clicked).
        
        THREE SCENARIOS:
        1. Recording in progress → Block close, warn user
        2. Metadata dialog open → Block close, warn user
        3. Clean state → Confirm exit
        
        Args:
            event: QCloseEvent
        """
        try:
            # Check recording state and dialog state
            is_recording = False
            is_dialog_open = False
            
            # Check if recording screen exists and has the helper methods
            if hasattr(self, 'recording_screen'):
                try:
                    is_recording = self.recording_screen.is_recording()
                    is_dialog_open = self.recording_screen.is_dialog_open()
                except Exception as e:
                    # If helper methods don't exist, assume safe to close
                    logger.warning(f"Could not check recording state: {e}")
            
            # Import CloseConfirmDialog
            from app.gui.dialogs import CloseConfirmDialog
            
            # Use CloseConfirmDialog to handle all three scenarios
            should_close = CloseConfirmDialog.handle_close(
                parent=self,
                is_recording=is_recording,
                is_dialog_open=is_dialog_open
            )
            
            if should_close:
                # Stop voice service if running (cleanup)
                if hasattr(self, 'voice_service') and self.voice_service:
                    if hasattr(self, 'voice_enabled') and self.voice_enabled:
                        try:
                            self.voice_service.stop_listening()
                            logger.info("Voice service stopped")
                        except Exception as e:
                            logger.warning(f"Voice cleanup error: {e}")
                
                # User confirmed exit - allow close
                logger.info("Application closing via user request (X button)")
                event.accept()
            else:
                # User needs to handle something first - block close
                logger.info("Close blocked - user must stop recording or close dialog first")
                event.ignore()
                
        except Exception as e:
            # If any error, log and allow close (fail-safe)
            logger.error(f"Close event handler error: {e}")
            event.accept()


__all__ = ['MainWindow']
