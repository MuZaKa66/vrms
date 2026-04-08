"""
File: app/gui/recording/ui_builder.py

UI Builder - Stateless Widget Factory for VRMS
Lahore General Hospital, Eye Department

All widgets follow design tokens from design_constants.py.
This module is STATELESS — it creates and returns widgets only.
Animation / timer state lives in the caller.

LINUX COMPATIBILITY NOTE:
  Raspberry Pi OS has no emoji font.  Every emoji (🌡 💾 🎥 etc.) renders
  as a white square.  All button labels in this file use plain text only.

Author: ZKB
Hospital: Lahore General Hospital - Eye Department
Date: April 1, 2026
Version: 3.1.0 (Visual polish pass)

Changelog:
  v3.1.0 - All emoji replaced with plain text for Linux compatibility
           - StatusPopup: centred on screen, coloured header, progress bar
           - create_preview_container: rounded bezel border, removed
             redundant recording_indicator (status_label now handles it)
           - create_temp_button:  "TEMP" text label
           - create_disk_button:  " SSD" text label
           - create_record_button: two-line text, updated size
           - create_status_label: larger font
  v3.0.0 - Initial VRMS redesign, top bar widgets added
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QWidget
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPixmap, QColor

from .design_constants import (
    SPACING, COLORS, SIZES, TIMINGS,
    get_info_button_style, get_record_button_style,
    get_vrm_logo_style, get_temp_button_style,
    get_disk_button_style, get_storage_bar_style,
    get_about_button_style,
)


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: UIBuilder — Stateless Widget Factory
# ═══════════════════════════════════════════════════════════════════════════════

class UIBuilder:
    """
    Stateless factory for all VRMS UI widgets.

    TOP BAR widgets (used by main_window.py):
        create_vrm_logo_button()    — square 3D logo, "VR / MS"
        create_temp_button()        — plain-text "TEMP" button
        create_disk_button()        — plain-text " SSD" button
        create_top_bar_clock()      — large centred date/time label

    RECORDING SCREEN widgets (used by recording_screen.py):
        create_status_label()       — "Ready to Record" / "● RECORDING"
        create_timer_label()        — large digital elapsed-time counter
        create_info_button()        — Add Info / Edit Info
        create_clear_button()       — Clear metadata
        create_info_display_label() — Patient / procedure text display
        create_record_button()      — START / STOP RECORDING
        create_preview_container()  — Bezel-styled video preview panel

    SHARED:
        update_recording_indicator() — update status_label blink text
    """

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: TOP BAR — VRM Logo Button
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_vrm_logo_button():
        """
        Create the VRM logo square button (top-left of top bar).

        Text: "VR" top line, "MS" bottom line — plain text, no emoji.
        Style: 3D press effect via asymmetric border shading.
        Size: SIZES['vrm_logo_button'] = (64, 56)

        Tap behaviour (expand animation) managed by main_window.py.

        Returns:
            QPushButton: Styled logo button
        """
        btn = QPushButton("VR\nMS")
        w, h = SIZES['vrm_logo_button']
        btn.setFixedSize(w, h)
        btn.setFont(QFont("Arial", SIZES['font_top_bar_icon'], QFont.Bold))
        btn.setStyleSheet(get_vrm_logo_style())
        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: TOP BAR — Temperature Button
    # Plain text "TEMP" + degree symbol.  No emoji.
    # Normal state: blue.  Warning (>TEMP_WARNING_THRESHOLD): red + flash.
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_temp_button():
        """
        Create the temperature status button for the top bar.

        Label:  "TEMP\n--.-°C"  (two lines — title + live reading)
        Normal: blue background
        Warning: red background (caller applies via set_temp_warning)
        Size: SIZES['temp_disk_button'] = (80, 56)

        Returns:
            QPushButton: Styled temperature button, initial normal state
        """
        btn = QPushButton("TEMP\n--.-°C")
        w, h = SIZES['temp_disk_button']
        btn.setFixedSize(w, h)
        btn.setFont(QFont("Arial", SIZES['font_top_bar_icon'] - 1, QFont.Bold))
        btn.setStyleSheet(get_temp_button_style(is_warning=False))
        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: TOP BAR — Disk Space Button
    # Plain text " SSD".  No emoji.
    # Normal: teal.  Warning (<DISK_WARNING_THRESHOLD_GB): amber + flash.
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_disk_button():
        """
        Create the disk space status button for the top bar.

        Label:  " SSD\n-- GB"  (two lines — title + live reading)
        Normal: teal background
        Warning: amber background (caller applies via set_disk_warning)
        Size: SIZES['temp_disk_button'] = (80, 56)

        Returns:
            QPushButton: Styled disk button, initial normal state
        """
        btn = QPushButton(" SSD\n-- GB")
        w, h = SIZES['temp_disk_button']
        btn.setFixedSize(w, h)
        btn.setFont(QFont("Arial", SIZES['font_top_bar_icon'] - 1, QFont.Bold))
        btn.setStyleSheet(get_disk_button_style(is_warning=False))
        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: TOP BAR — Clock Label
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_top_bar_clock():
        """
        Create the centred date/time label for the top bar.

        Format updated by main_window._update_clock() every second:
            "Wed  01 Apr 2026  14:35:22"
        Font: SIZES['font_top_bar_clock'] = 34px Bold

        Returns:
            QLabel: Clock label, initially empty
        """
        label = QLabel("")
        label.setFont(QFont("Arial", SIZES['font_top_bar_clock'], QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            f"color: {COLORS['status_bar_text']}; background: transparent;"
        )
        return label

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING SCREEN — Status Label
    # Positioned ABOVE the preview (right column).
    # Idle:      "Ready to Record"
    # Recording: "● RECORDING" (blinks via dot_blink_timer)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_status_label():
        """
        Create the status label shown above the preview panel.

        Idle state:      "Ready to Record"  — danger red
        Recording state: "● RECORDING"      — danger red, blinks

        Font: SIZES['font_status'] = 26px Bold

        Returns:
            QLabel: Status label with initial "Ready to Record" text
        """
        label = QLabel("Ready to Record")
        label.setFont(QFont("Arial", SIZES['font_status'], QFont.Bold))
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setStyleSheet(
            f"color: {COLORS['danger']}; background: transparent;"
        )
        label.setFixedHeight(40)
        return label

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING SCREEN — Timer Label
    # Positioned ABOVE the record button (left column).
    # Hidden in idle state; shown when recording starts.
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_timer_label():
        """
        Create the large digital elapsed-time label.

        Shown only during active recording (above the record button).
        Initially hidden — _update_ui_for_recording() calls setVisible(True).
        Font: SIZES['font_timer'] = 52px Bold

        Returns:
            QLabel: Timer label, initially hidden, text "00:00:00"
        """
        label = QLabel("00:00:00")
        label.setFont(QFont("Arial", SIZES['font_timer'], QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            f"color: {COLORS['danger']}; background: transparent;"
        )
        label.setVisible(False)
        return label

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING SCREEN — Add Info Button
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_info_button(has_info=False):
        """
        Create the Add Info / Edit Info button.

        Args:
            has_info (bool): False → "Add Info" blue, True → "Edit Info" amber

        Size: SIZES['info_button'] = (220, 65)

        Returns:
            QPushButton: Info button
        """
        text = "Edit Info" if has_info else "Add Info"
        btn = QPushButton(text)
        w, h = SIZES['info_button']
        btn.setFixedSize(w, h)
        btn.setFont(QFont("Arial", SIZES['font_button_secondary'], QFont.Bold))
        btn.setStyleSheet(get_info_button_style(has_info))
        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING SCREEN — Clear Button
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_clear_button():
        """
        Create the Clear metadata button.

        Initially hidden (setVisible(False)).
        Shown by metadata_handler when info exists.

        Returns:
            QPushButton: Clear button, initially hidden
        """
        btn = QPushButton("Clear")
        btn.setFixedSize(120, SIZES['info_button'][1])
        btn.setFont(QFont("Arial", SIZES['font_button_secondary'], QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['text_secondary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {SIZES['font_button_secondary']}px;
                font-weight: bold;
            }}
            QPushButton:hover   {{ background-color: {COLORS['border_dark']}; }}
            QPushButton:pressed {{ background-color: {COLORS['text_muted']}; }}
        """)
        btn.setVisible(False)
        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING SCREEN — Info Display Label
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_info_display_label():
        """
        Create the patient / procedure text display label.

        Shown after Add Info is used.
        Color: LGH success green.

        Returns:
            QLabel: Info display label, initially empty
        """
        label = QLabel("")
        label.setFont(QFont("Arial", SIZES['font_info_display']))
        label.setStyleSheet(
            f"color: {COLORS['success']}; font-weight: bold; background: transparent;"
        )
        label.setWordWrap(True)
        return label

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING SCREEN — Record Button
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_record_button(is_recording=False):
        """
        Create the START / STOP RECORDING button.

        Two-line text fits the large button area.
        CRITICAL: setFixedSize only — setMinimumSize/setMaximumSize conflict
        with setFixedSize and cause Qt to collapse the button height.

        Size: SIZES['record_button'] = (490, 275)

        Args:
            is_recording (bool): False → green START, True → red STOP

        Returns:
            QPushButton: Record button
        """
        text = "STOP\nRECORDING" if is_recording else "START\nRECORDING"
        btn = QPushButton(text)
        w, h = SIZES['record_button']
        btn.setFixedSize(w, h)   # CRITICAL: only setFixedSize
        btn.setFont(QFont("Arial", SIZES['font_button_primary'], QFont.Bold))
        btn.setStyleSheet(get_record_button_style(is_recording))
        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: RECORDING SCREEN — Preview Container
    # Bezel-styled frame with rounded corners.
    # recording_indicator removed — status_label above preview replaces it.
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_preview_container():
        """
        Create the live video preview container (right column, below status_label).

        Visual design:
          - Outer QFrame: darker border for depth (bezel outer edge)
          - Inner QLabel:  rounded 12px corners, dark background, inner border
          This gives a "screen set in a bezel" appearance instead of a plain box.

        CRITICAL: Only setFixedSize on preview_label — no setMinimumSize /
        setMaximumSize (they override setFixedSize and collapse to black strip).

        Returns:
            tuple: (container, preview_label, preview_buffer)
                container     — QFrame outer wrapper
                preview_label — QLabel for setPixmap() video frames
                preview_buffer — QPixmap initial dark buffer
        """
        container = QFrame()
        container.setObjectName("PreviewContainer")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(3, 3, 3, 3)   # creates the outer bezel gap
        layout.setSpacing(0)

        # ── Preview display label ─────────────────────────────────────────────
        preview_label = QLabel()
        pw, ph = SIZES['preview']
        preview_label.setFixedSize(pw, ph)       # CRITICAL: only setFixedSize
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['preview_bg']};
                border: 2px solid {COLORS['preview_border']};
                border-radius: 12px;
                color: {COLORS['text_light']};
            }}
        """)

        # Outer container gets the deeper bezel border
        container.setStyleSheet(f"""
            QFrame#PreviewContainer {{
                background-color: {COLORS['preview_border_outer']};
                border: 2px solid {COLORS['preview_border_outer']};
                border-radius: 14px;
            }}
        """)

        # ── Double-buffer pixmap ──────────────────────────────────────────────
        preview_buffer = QPixmap(pw, ph)
        preview_buffer.fill(QColor(COLORS['preview_bg']))
        preview_label.setPixmap(preview_buffer)

        layout.addWidget(preview_label)

        # Fix container size: preview + 6px (3px bezel each side)
        container.setFixedSize(pw + 6, ph + 6)

        return container, preview_label, preview_buffer

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: SHARED — Recording Indicator Update
    # Updates status_label blink text during recording.
    # Called by dot_blink_timer every TIMINGS['dot_blink'] ms.
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def update_recording_indicator(status_label, visible=True):
        """
        Blink the "● RECORDING" status label above the preview.

        In v3.1 the recording_indicator label inside the preview container
        has been removed.  The status_label (above preview, right column)
        now serves as the recording indicator.

        Args:
            status_label (QLabel): The status label widget
            visible (bool):
                True  → bright red "● RECORDING"
                False → dimmed red "● RECORDING" (blink-off state)
        """
        if visible:
            status_label.setStyleSheet(
                f"color: {COLORS['danger']}; "
                f"font-weight: bold; background: transparent;"
            )
        else:
            # Dim the colour slightly on blink-off (text stays, just fades)
            status_label.setStyleSheet(
                f"color: {COLORS['danger_pressed']}; "
                f"font-weight: bold; background: transparent;"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: StatusPopup — Centred Non-Blocking Status Card
#
# Appears in the CENTRE of the parent window (not anchored to buttons).
# Has a coloured header bar, content text, optional progress bar.
# Auto-dismisses after TIMINGS['popup_dismiss'] ms.
# Has a manual close button in the header.
#
# Usage (from main_window.py):
#     popup = StatusPopup(
#         parent=self,
#         title="TEMPERATURE",
#         header_color=COLORS['popup_header_temp'],
#         lines=["Current:  42.0 °C", "Status: Normal"],
#         is_warning=False,
#     )
#     popup.show_popup()
# ═══════════════════════════════════════════════════════════════════════════════

class StatusPopup(QFrame):
    """
    Centred non-blocking popup card for temp / disk status.

    Layout:
      ┌─────────────────────────────────────────────┐
      │  TITLE                                  [X] │  ← coloured header
      ├─────────────────────────────────────────────┤
      │  Primary line                               │
      │  Secondary line(s)                          │
      │  [████████████░░░░░░░░  progress bar]       │  optional
      └─────────────────────────────────────────────┘

    Args:
        parent (QWidget):       Parent window (used for centring)
        title (str):            Header bar title text
        header_color (str):     Hex colour for the header bar
        lines (list[str]):      Body text lines (first line is primary)
        is_warning (bool):      True → amber border, False → blue border
        progress_pct (int|None):If set, adds a progress bar at this %
        progress_level (str):   'ok' / 'low' / 'critical' for bar colour
    """

    def __init__(
        self,
        parent,
        title,
        header_color,
        lines,
        is_warning=False,
        progress_pct=None,
        progress_level='ok',
        bar_label=None,            # ← ADD THIS LINE after 493
    ):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # ── Outer frame border (warning → amber, normal → blue) ──────────────
        border_col = COLORS['disk_warning'] if is_warning else COLORS['info']
        self.setObjectName("StatusPopupFrame")
        self.setStyleSheet(f"""
            QFrame#StatusPopupFrame {{
                background-color: {COLORS['popup_bg']};
                border: 3px solid {border_col};
                border-radius: 12px;
            }}
        """)
        self.setMinimumWidth(SIZES['popup_width'])

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("PopupHeader")
        header.setAttribute(Qt.WA_StyledBackground, True)
        header.setStyleSheet(f"""
            QWidget#PopupHeader {{
                background-color: {header_color};
                border-radius: 9px 9px 0 0;
            }}
        """)

        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(16, 10, 10, 10)
        hdr_layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Arial", SIZES['font_popup_title'], QFont.Bold))
        title_lbl.setStyleSheet(
            "color: white; background: transparent; border: none;"
        )
        hdr_layout.addWidget(title_lbl)
        hdr_layout.addStretch()

        # Manual close button (also auto-dismissed by timer)
        close_btn = QPushButton("X")
        close_btn.setFixedSize(34, 34)
        close_btn.setFont(QFont("Arial", 13, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,60);
                color: white;
                border: none;
                border-radius: 17px;
                font-weight: bold;
            }
            QPushButton:pressed { background-color: rgba(255,255,255,120); }
        """)
        close_btn.clicked.connect(self.close)
        hdr_layout.addWidget(close_btn)

        outer.addWidget(header)

        # ── Body ──────────────────────────────────────────────────────────────
        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(18, 14, 18, 16)
        body_layout.setSpacing(8)

        for i, line in enumerate(lines):
            lbl = QLabel(line)
            if i == 0:
                lbl.setFont(QFont("Arial", SIZES['font_popup'], QFont.Bold))
                lbl.setStyleSheet(
                    f"color: {COLORS['popup_text']}; "
                    f"background: transparent; border: none;"
                )
            else:
                lbl.setFont(QFont("Arial", SIZES['font_popup_small']))
                col = COLORS['danger'] if is_warning else COLORS['popup_text']
                lbl.setStyleSheet(
                    f"color: {col}; background: transparent; border: none;"
                )
            body_layout.addWidget(lbl)

        # Optional progress bar
        if progress_pct is not None:
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(100)
            bar.setValue(int(progress_pct))
            bar.setFixedHeight(28)
           # bar.setFormat(f"  {progress_pct}% used")
            bar.setFormat(f"  {bar_label}" if bar_label else f"  {progress_pct}% used")
            bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            bar.setStyleSheet(get_storage_bar_style(progress_level))
            body_layout.addWidget(bar)

        outer.addLayout(body_layout)

        # ── Auto-dismiss timer ────────────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)

    def show_popup(self):
        """
        Centre popup on the parent window and show it.

        Centering:
          - Horizontal: (parent_width  - popup_width)  / 2
          - Vertical:   (parent_height - popup_height) / 2
          Maps from parent-local to global screen coordinates.

        Starts auto-dismiss timer (TIMINGS['popup_dismiss'] ms).
        """
        self.adjustSize()

        parent = self.parent()
        if parent:
            g = parent.mapToGlobal(QPoint(0, 0))
            x = g.x() + (parent.width()  - self.width())  // 2
            y = g.y() + (parent.height() - self.height()) // 2
            self.move(x, y)

        self.show()
        self.raise_()
        self.activateWindow()
        self._timer.start(TIMINGS['popup_dismiss'])


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = ['UIBuilder', 'StatusPopup']
