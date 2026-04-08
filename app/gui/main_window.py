"""
File: app/gui/main_window.py

Video Recording Management System - Main Window
Lahore General Hospital, Eye Department

TOP BAR (left -> right, 70px):
  [VR/MS]  [TEMP / xx.x°C]  [SSD / xx GB]  |  Wed 01 Apr 2026  14:35 | [X]

  - VRM logo:   tap to expand full app name for 2s then collapse
  - TEMP btn:   shows live temp reading; blue (ok) / red+flash (>55°C)
                tap -> centred StatusPopup with reading
  - SSD btn:    shows live free GB; teal (ok) / amber+flash (<5 GB)
                tap -> centred StatusPopup with bar
  - Clock:      centred, 34px, "Day  DD Mon YYYY  HH:MM:SS"
  - Close (X):  checks recording state before exiting, no tooltip

NAV BAR (bottom, 90px):
  [  REC  ]  [  LIB  ]  [  SET  ]   — LGH green, 20px font, plain text

Author: ZKB / OT Video Dev Team
Hospital: Lahore General Hospital - Eye Department
Date: April 1, 2026
Version: 4.1.0 (Visual polish pass)

Changelog:
  v4.1.0 - Top bar background: lighter slate #4a6278
           - TEMP / SSD buttons show live reading as second line
           - Removed setToolTip from close button
           - Nav buttons: LGH green, "REC/LIB/SET" plain text, font 20px
           - StatusPopup: centred, coloured header, progress bar
           - All emoji removed (Linux has no emoji font)
  v4.0.0 - Full VRMS top bar redesign
  v3.1.0 - Robust voice error handling
"""
#test zb 

from datetime import datetime
import shutil

from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox,
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

from app.gui.recording.design_constants import (
    COLORS, SIZES, TIMINGS,
    TEMP_WARNING_THRESHOLD,
    DISK_WARNING_THRESHOLD_GB,
    get_temp_button_style,
    get_disk_button_style,
    get_nav_button_style,
)
from app.gui.recording.ui_builder import UIBuilder, StatusPopup

# ── Voice (OPTIONAL — app works fully without it) ─────────────────────────────
try:
    from app.services.voice_command_service import VoiceCommandService
    from app.gui.widgets.voice_indicator_widget import VoiceIndicatorWidget
    VOICE_AVAILABLE = True    # Dependencies verified OK
except ImportError:
    VOICE_AVAILABLE = False

logger = AppLogger("MainWindow")


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS: MainWindow
# ═══════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """
    Root application window for the Video Recording Management System.

    Attributes:
        system_monitor  (SystemMonitorService)
        voice_service   (VoiceCommandService | None)
        voice_indicator (VoiceIndicatorWidget | None)
        voice_enabled   (bool)

        top_bar         (QWidget)       70px top bar
        nav_bar         (QWidget)       90px bottom nav bar
        screens         (QStackedWidget)

        vrm_btn         (QPushButton)   VRM logo
        temp_btn        (QPushButton)   Temperature
        disk_btn        (QPushButton)   Disk space
        clock_label     (QLabel)        Live date/time
        vrm_expand_label(QLabel)        Full app name (during animation)

        recording_screen (RecordingScreen)
        library_screen   (LibraryScreen)
        playback_screen  (PlaybackScreen)
        settings_screen  (SettingsScreen)

        _temp_is_warning (bool)
        _disk_is_warning (bool)
        _temp_flash_state(bool)
        _disk_flash_state(bool)
        _last_temp_c     (float)
        _last_free_gb    (float)
        _vrm_expanding   (bool)
        _temp_popup      (StatusPopup | None)
        _disk_popup      (StatusPopup | None)
    """

    def __init__(self):
        super().__init__()

        self.system_monitor = SystemMonitorService()

        self.voice_service   = None
        self.voice_indicator = None
        self.voice_enabled   = False

        # Flash / animation state
        self._temp_is_warning  = False
        self._disk_is_warning  = False
        self._temp_flash_state = True
        self._disk_flash_state = True
        self._vrm_expanding    = False
        self._last_temp_c      = 0.0
        self._last_free_gb     = 0.0
        self._last_total_gb    = 0.0

        # Popup references kept alive until auto-dismissed
        self._temp_popup = None
        self._disk_popup = None

        self.init_ui()
        self.init_voice()
        self._start_system_monitoring()

        self.showFullScreen()
        logger.info(
            f"MainWindow initialised — {self.width()}x{self.height()}"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: UI INITIALISATION
    # ─────────────────────────────────────────────────────────────────────────

    def init_ui(self):
        """
        Build main window layout:
          QVBoxLayout
            top_bar  (70px)
            screens  (stretch=1)
            nav_bar  (90px)
        """
        self.setWindowTitle("Video Recording Management System")
        self.setMinimumSize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.top_bar = self._create_top_status_bar()
        main_layout.addWidget(self.top_bar)

        self.screens = QStackedWidget()
        main_layout.addWidget(self.screens, stretch=1)

        self.recording_screen = RecordingScreen()
        self.library_screen   = LibraryScreen(self)
        self.playback_screen  = PlaybackScreen()
        self.settings_screen  = SettingsScreen()

        self.screens.addWidget(self.recording_screen)
        self.screens.addWidget(self.library_screen)
        self.screens.addWidget(self.playback_screen)
        self.screens.addWidget(self.settings_screen)

        self.playback_screen.back_clicked.connect(self.show_library_screen)

        self.nav_bar = self._create_bottom_nav_bar()
        main_layout.addWidget(self.nav_bar)

        self.show_recording_screen()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: TOP STATUS BAR  (70px)
    # Left→right: VRM logo | TEMP | SSD | [stretch] clock [stretch] | Close
    # ─────────────────────────────────────────────────────────────────────────

    def _create_top_status_bar(self):
        """
        Build the 70px top status bar.

        Stores widgets as instance attributes for later updates:
          self.vrm_btn, self.temp_btn, self.disk_btn,
          self.clock_label, self.vrm_expand_label

        Returns:
            QWidget: Configured top bar
        """
        bar = QWidget()
        bar.setFixedHeight(SIZES['top_bar_height'])
        bar.setStyleSheet(
            f"QWidget {{ background-color: {COLORS['status_bar_bg']}; }}"
        )

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(8)

        # ── 1. VRM logo ───────────────────────────────────────────────────────
        self.vrm_btn = UIBuilder.create_vrm_logo_button()
        self.vrm_btn.clicked.connect(self._on_vrm_logo_clicked)
        layout.addWidget(self.vrm_btn)
        layout.addSpacing(9)        # ← add this line — gap between VRM and TEMP

        # ── 2. Temperature button ─────────────────────────────────────────────
        self.temp_btn = UIBuilder.create_temp_button()
        self.temp_btn.clicked.connect(self._on_temp_button_clicked)
        layout.addWidget(self.temp_btn)
        layout.addSpacing(9)        # ← add this line — gap between VRM and TEMP

        # ── 3. Disk space button ──────────────────────────────────────────────
        self.disk_btn = UIBuilder.create_disk_button()
        self.disk_btn.clicked.connect(self._on_disk_button_clicked)
        layout.addWidget(self.disk_btn)

        # ── VRM expand label (hidden; shown during animation) ─────────────────
        self.vrm_expand_label = QLabel("Video Recording Management System")
        self.vrm_expand_label.setFont(
            QFont("Arial", SIZES['font_top_bar_icon'] + 2, QFont.Bold)
        )
        self.vrm_expand_label.setAlignment(Qt.AlignCenter)
        self.vrm_expand_label.setStyleSheet(
            f"color: {COLORS['status_bar_text']}; background: transparent;"
        )
        self.vrm_expand_label.setVisible(False)
        layout.addWidget(self.vrm_expand_label, stretch=1)

        # ── 4. Clock label (takes remaining centred space) ────────────────────
        self.clock_label = UIBuilder.create_top_bar_clock()
        layout.addWidget(self.clock_label, stretch=1)

        # ── 5. Close button — NO tooltip (self-explanatory ✕) ─────────────────
        close_w, close_h = SIZES['close_button']
        exit_btn = QPushButton("X")
        exit_btn.setFixedSize(close_w, close_h)
        exit_btn.setFont(QFont("Arial", 34, QFont.Bold))
        # No setToolTip — tooltip banner was too small to read
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: {close_h // 2}px;
                font-weight: bold;
            }}
            QPushButton:hover   {{ background-color: {COLORS['danger_hover']}; }}
            QPushButton:pressed {{ background-color: {COLORS['danger_pressed']}; }}
        """)
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)

        return bar

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: VRM LOGO ANIMATION
    # Tap → hide icons + show full app name for vrm_expand_show ms → collapse
    # ─────────────────────────────────────────────────────────────────────────

    def _on_vrm_logo_clicked(self):
        """
        Start VRM expand animation.
        Hides temp_btn, disk_btn, clock_label;
        shows vrm_expand_label for TIMINGS['vrm_expand_show'] ms.
        """
        if self._vrm_expanding:
            return
        self._vrm_expanding = True
        self.temp_btn.setVisible(False)
        self.disk_btn.setVisible(False)
        self.clock_label.setVisible(False)
        self.vrm_expand_label.setVisible(True)
        QTimer.singleShot(TIMINGS['vrm_expand_show'], self._collapse_vrm_expand)

    def _collapse_vrm_expand(self):
        """Restore normal top bar state after VRM expand animation."""
        self.vrm_expand_label.setVisible(False)
        self.clock_label.setVisible(True)
        self.temp_btn.setVisible(True)
        self.disk_btn.setVisible(True)
        self._vrm_expanding = False

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: TEMPERATURE BUTTON LOGIC
    # ─────────────────────────────────────────────────────────────────────────

    def _set_temp_warning(self, is_warning):
        """
        Switch temperature button between normal (blue) and warning (red).
        Starts or stops the flash timer accordingly.

        Args:
            is_warning (bool): True → red + flash, False → blue solid
        """
        if is_warning == self._temp_is_warning:
            return
        self._temp_is_warning = is_warning
        self.temp_btn.setStyleSheet(get_temp_button_style(is_warning))
        if is_warning:
            if not self._temp_flash_timer.isActive():
                self._temp_flash_timer.start(TIMINGS['flash_interval'])
        else:
            self._temp_flash_timer.stop()
            self.temp_btn.setVisible(True)

    def _toggle_temp_flash(self):
        """Blink temp button visibility (called by _temp_flash_timer)."""
        if not self._temp_is_warning:
            return
        self._temp_flash_state = not self._temp_flash_state
        self.temp_btn.setVisible(self._temp_flash_state)

    def _on_temp_button_clicked(self):
        """
        Show centred temperature StatusPopup when button is tapped.

        Normal:  current temp + "Status: Normal"
        Warning: current temp + advice to move to cooler location

        Non-blocking, auto-dismisses after TIMINGS['popup_dismiss'] ms.
        """
        self.temp_btn.setVisible(True)   # ensure visible if tapped during flash-off
        temp = self._last_temp_c

        if self._temp_is_warning:
            lines = [
                f"Current:  {temp:.1f} °C   (limit: {TEMP_WARNING_THRESHOLD} °C)",
                "WARNING: Temperature is high",
                "Please move the system to a cooler location",
                "or improve airflow around the device.",
            ]
            hdr = COLORS['popup_header_temp_w']
        elif temp > 0:
            lines = [
                f"Current:  {temp:.1f} °C   (limit: {TEMP_WARNING_THRESHOLD} °C)",
                "Status: Normal  OK",
            ]
            hdr = COLORS['popup_header_temp']
        else:
            lines = ["Temperature sensor not available on this platform."]
            hdr = COLORS['popup_header_temp']

        # Progress bar: temp as % of warning threshold (100% = at threshold)
        pct = int(min((temp / TEMP_WARNING_THRESHOLD) * 100, 100)) if temp > 0 else 0
        lvl = 'temp'    # always blue bar for temperature

        self._temp_popup = StatusPopup(
            parent=self,
            title="TEMPERATURE",
            header_color=hdr,
            lines=lines,
            is_warning=self._temp_is_warning,
            progress_pct=pct if temp > 0 else None,
            progress_level=lvl,
            bar_label=f"{temp:.1f} °C  (limit: {TEMP_WARNING_THRESHOLD} °C)",  # ← ADD
        )
        self._temp_popup.show_popup()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: DISK SPACE BUTTON LOGIC
    # ─────────────────────────────────────────────────────────────────────────

    def _set_disk_warning(self, is_warning):
        """
        Switch disk button between normal (teal) and warning (amber).

        Args:
            is_warning (bool): True → amber + flash, False → teal solid
        """
        if is_warning == self._disk_is_warning:
            return
        self._disk_is_warning = is_warning
        self.disk_btn.setStyleSheet(get_disk_button_style(is_warning))
        if is_warning:
            if not self._disk_flash_timer.isActive():
                self._disk_flash_timer.start(TIMINGS['flash_interval'])
        else:
            self._disk_flash_timer.stop()
            self.disk_btn.setVisible(True)

    def _toggle_disk_flash(self):
        """Blink disk button visibility (called by _disk_flash_timer)."""
        if not self._disk_is_warning:
            return
        self._disk_flash_state = not self._disk_flash_state
        self.disk_btn.setVisible(self._disk_flash_state)

    def _on_disk_button_clicked(self):
        """
        Show centred disk space StatusPopup when button is tapped.

        Always shows free GB, total GB, and a horizontal usage bar.
        Warning state adds a "free up space" message.

        Non-blocking, auto-dismisses after TIMINGS['popup_dismiss'] ms.
        """
        self.disk_btn.setVisible(True)

        # Use stored values from monitoring — no duplicate disk_usage call
        free_gb  = self._last_free_gb
        total_gb = self._last_total_gb
        pct_free = int(((total_gb - free_gb) / total_gb) * 100) if total_gb > 0 else 0

        bar_level = (
            'critical' if free_gb < 2 else
            'low'      if free_gb < DISK_WARNING_THRESHOLD_GB else
            'ok'
        )

        if self._disk_is_warning:
            lines = [
                f"Free:  {free_gb:.1f} GB   of   {total_gb:.1f} GB",
                "WARNING: Storage is running low",
                "Export recordings to USB or delete old files",
                "to free up space.",
            ]
            hdr = COLORS['popup_header_disk_w']
        else:
            lines = [
                f"Free:  {free_gb:.1f} GB   of   {total_gb:.1f} GB",
                "Storage: Adequate  OK",
            ]
            hdr = COLORS['popup_header_disk']

        self._disk_popup = StatusPopup(
            parent=self,
            title="STORAGE  (SSD)",
            header_color=hdr,
            lines=lines,
            is_warning=self._disk_is_warning,
            progress_pct=pct_free,
            progress_level=bar_level,
        )
        self._disk_popup.show_popup()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: BOTTOM NAVIGATION BAR  (90px)
    # Plain text labels: "REC" / "LIB" / "SET" — no emoji (Linux compat)
    # LGH green buttons on dark background for high visibility
    # ─────────────────────────────────────────────────────────────────────────

    def _create_bottom_nav_bar(self):
        """
        Build the 90px bottom navigation bar.

        Button labels are plain ASCII — no emoji on Raspberry Pi OS.

        Returns:
            QWidget: Configured navigation bar
        """
        bar = QWidget()
        bar.setFixedHeight(SIZES['nav_bar_height'])
        bar.setStyleSheet(
            f"background-color: {COLORS['nav_bar_bg']};"
        )

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(15)

        btn_rec = self._create_nav_button("REC")
        btn_rec.clicked.connect(self.show_recording_screen)
        layout.addWidget(btn_rec)

        btn_lib = self._create_nav_button("LIB")
        btn_lib.clicked.connect(self.show_library_screen)
        layout.addWidget(btn_lib)

        btn_set = self._create_nav_button("SET")
        btn_set.clicked.connect(self.show_settings_screen)
        layout.addWidget(btn_set)

        return bar

    def _create_nav_button(self, text):
        """
        Create a single bottom navigation button.

        Args:
            text (str): Button label (plain ASCII, no emoji)

        Returns:
            QPushButton: Styled navigation button
        """
        btn = QPushButton(text)
        btn.setMinimumSize(200, SIZES['nav_button_height'])
        btn.setFont(QFont("Arial", SIZES['font_nav_button'], QFont.Bold))
        btn.setStyleSheet(get_nav_button_style())
        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: SCREEN NAVIGATION
    # ─────────────────────────────────────────────────────────────────────────

    def show_recording_screen(self):
        """Switch to recording screen."""
        self.screens.setCurrentWidget(self.recording_screen)

    def show_library_screen(self):
        """Switch to library screen and refresh content."""
        self.library_screen.refresh()
        self.screens.setCurrentWidget(self.library_screen)

    def show_settings_screen(self):
        """Switch to settings screen."""
        self.screens.setCurrentWidget(self.settings_screen)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: SYSTEM MONITORING
    # ─────────────────────────────────────────────────────────────────────────

    def _start_system_monitoring(self):
        """
        Initialise all periodic timers:
          _monitor_timer:     health poll every 5s
          _clock_timer:       clock update every 1s
          _temp_flash_timer:  500ms flash (started on demand)
          _disk_flash_timer:  500ms flash (started on demand)
        """
        # Flash timers MUST be created first — _update_system_status uses them
        self._temp_flash_timer = QTimer(self)
        self._temp_flash_timer.timeout.connect(self._toggle_temp_flash)
        self._monitor_timer = QTimer(self)
        # Now safe to call _update_system_status
        self._monitor_timer.timeout.connect(self._update_system_status)
        self._monitor_timer.start(5000)
        self._update_system_status()

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(TIMINGS['clock_update'])
        self._update_clock()

        self._temp_flash_timer = QTimer(self)
        self._temp_flash_timer.timeout.connect(self._toggle_temp_flash)

        self._disk_flash_timer = QTimer(self)
        self._disk_flash_timer.timeout.connect(self._toggle_disk_flash)

    def _update_system_status(self):
        """
        Poll SystemMonitorService and update top bar button states.

        Also updates the button second-line text (live temp / free GB reading)
        so the user can see current values without tapping.

        Temperature threshold: TEMP_WARNING_THRESHOLD (55°C)
        Disk threshold:        DISK_WARNING_THRESHOLD_GB (5.0 GB)
        """
        success, health, error = self.system_monitor.get_system_health()
        if not success:
            logger.warning(f"Health check failed: {error}")
            return

        # ── Temperature ───────────────────────────────────────────────────────
        temp = health.get('temperature', 0.0)
        self._last_temp_c = temp
        self._set_temp_warning(temp > TEMP_WARNING_THRESHOLD and temp > 0)

        # Update button label with live reading
        if temp > 0:
            self.temp_btn.setText(f"TEMP\n{temp:.1f}°C")
        else:
            self.temp_btn.setText("TEMP\n--.-°C")

        # ── Disk space (SSD) ──────────────────────────────────────────────────
        free_gb = health.get('storage_gb', 0.0)
        self._last_free_gb = free_gb
        # Store total GB once here — reused by popup (no duplicate disk_usage call)
        try:
            from config.app_config import VIDEO_STORAGE_PATH
            _dt, _du, _df = shutil.disk_usage(VIDEO_STORAGE_PATH)
            self._last_total_gb = _dt / (1024 ** 3)
        except Exception:
            self._last_total_gb = 0.0
        self._set_disk_warning(free_gb < DISK_WARNING_THRESHOLD_GB)

        # Update button label with live reading
        self.disk_btn.setText(f" SSD\n{free_gb:.0f} GB")

    def _update_clock(self):
        """
        Refresh the top bar clock label.
        Format: "Wed  01 Apr 2026  14:35:22"
        """
        try:
            now = datetime.now()
            self.clock_label.setText(now.strftime("%a  %d %b %Y  %H:%M:%S"))
        except Exception as e:
            logger.error(f"Clock update error: {e}")
            self.clock_label.setText("--:--:--")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: VOICE COMMAND INTEGRATION  (optional)
    # ─────────────────────────────────────────────────────────────────────────

    def init_voice(self):
        """Initialise voice commands (OPTIONAL). Errors do not affect recording."""
        if not VOICE_AVAILABLE:
            logger.info("Voice commands not available")
            return
        try:
            self.voice_service = VoiceCommandService()
            if not self.voice_service.is_available():
                return
            self.voice_service.set_command_callback(self.handle_voice_command)
            self.voice_indicator = VoiceIndicatorWidget(self)
            self.voice_indicator.move(self.width() - 140, self.height() - 140)
            self.voice_indicator.hide()
            logger.info("Voice commands initialised")
        except Exception as e:
            logger.error(f"Voice init error: {e}")
            self.voice_service = None

    def toggle_voice(self):
        """Toggle voice listening on/off."""
        if not self.voice_service:
            QMessageBox.information(
                self, "Voice Unavailable",
                "Voice commands require:\n\n"
                "1. Vosk package: pip install vosk\n"
                "2. Vosk model in ~/vosk-models/\n"
                "3. Working microphone\n\n"
                "App works fine without voice!"
            )
            return
        if not self.voice_enabled:
            success, error = self.voice_service.start_listening()
            if success:
                self.voice_enabled = True
                if self.voice_indicator:
                    self.voice_indicator.show()
                    self.voice_indicator.set_idle()
            else:
                QMessageBox.warning(
                    self, "Voice Error",
                    f"Cannot start voice:\n\n{error}\n\n"
                    "Recording works fine without voice!"
                )
        else:
            self.voice_service.stop_listening()
            self.voice_enabled = False
            if self.voice_indicator:
                self.voice_indicator.hide()

    def handle_voice_command(self, command: str):
        """Route voice commands. Errors are caught and logged."""
        logger.info(f"Voice command: {command}")
        if command.startswith("voice_error:"):
            error_msg = command.split(":", 1)[1]
            if self.voice_indicator:
                self.voice_indicator.set_error("Error")
            self.voice_enabled = False
            QMessageBox.warning(
                self, "Voice Error",
                f"Voice recognition stopped:\n\n{error_msg}"
            )
            return
        if command == "wake_word_detected":
            if self.voice_indicator:
                self.voice_indicator.set_listening()
            return
        if self.voice_indicator:
            self.voice_indicator.set_recognized()
        try:
            if command == "start_recording":
                self.show_recording_screen()
                self.recording_screen.voice_start_recording()
            elif command == "stop_recording":
                if self.recording_screen.is_recording():
                    self.recording_screen.voice_stop_recording()
            elif command == "go_to_library":
                self.show_library_screen()
            elif command == "go_to_settings":
                self.show_settings_screen()
        except Exception as e:
            logger.error(f"Voice command error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: WINDOW EVENTS
    # ─────────────────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        """Keep voice indicator in bottom-right corner."""
        super().resizeEvent(event)
        if self.voice_indicator:
            self.voice_indicator.move(
                self.width() - 140, self.height() - 140
            )

    def closeEvent(self, event):
        """
        Handle close request from the red X button.

        Scenarios handled by CloseConfirmDialog.handle_close():
          1. Recording active  → block, warn user to stop first
          2. Dialog open       → block, warn user to close dialog
          3. Clean             → confirm exit

        Stops flash timers and voice service before exiting.
        """
        try:
            is_recording   = False
            is_dialog_open = False
            if hasattr(self, 'recording_screen'):
                try:
                    is_recording   = self.recording_screen.is_recording()
                    is_dialog_open = self.recording_screen.is_dialog_open()
                except Exception as e:
                    logger.warning(f"State check error: {e}")

            should_close = CloseConfirmDialog.handle_close(
                parent=self,
                is_recording=is_recording,
                is_dialog_open=is_dialog_open,
            )

            if should_close:
                # Stop timers
                for timer_name in ('_temp_flash_timer', '_disk_flash_timer',
                                   '_monitor_timer', '_clock_timer'):
                    t = getattr(self, timer_name, None)
                    if t:
                        t.stop()
                # Stop voice
                if self.voice_service and self.voice_enabled:
                    try:
                        self.voice_service.stop_listening()
                    except Exception as e:
                        logger.warning(f"Voice cleanup error: {e}")
                logger.info("Application closing — confirmed")
                event.accept()
            else:
                logger.info("Close blocked — recording or dialog active")
                event.ignore()

        except Exception as e:
            logger.error(f"Close event error: {e}")
            event.accept()   # fail-safe


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = ['MainWindow']
