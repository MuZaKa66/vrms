"""
File: app/gui/recording/design_constants.py

Design Constants - LGH Branded UI Design System
Video Recording Management System (VRMS)

Colors extracted from Lahore General Hospital logo:
  - Deep Green  (#1a6b2a) - Shield border
  - Crimson Red (#cc1414) - Crescent moon
  - Royal Blue  (#1a3fa0) - Hospital banner

Target Hardware:
  - 7-inch LCD touchscreen, 1024x600 resolution
  - Raspberry Pi 4 / Linux — NO emoji font installed,
    all icons use plain ASCII / Unicode text only
  - Gloved hands, visibility at 2-3 metres

Author: ZKB
Special Thanks: Dr. Farqaleet
Hospital: Lahore General Hospital - Eye Department
Date: April 1, 2026
Version: 4.1.0 (Visual polish pass)

Changelog:
  v4.1.0 - Top bar lighter slate (#4a6278 replaces near-black #1e2d3d)
           - All emoji replaced with plain text for Linux compatibility
           - Popup redesigned: centred on screen, coloured header, bar
           - Preview bezel: rounded corners + deeper border for screen look
           - Nav buttons: LGH green, larger font 18->20
           - Clock font 28->34, info_button height 52->65
           - Two-column controls layout sizes recalculated
           - TEMP/SSD button sizes widened for text labels
  v4.0.0 - Full VRMS redesign, top bar consolidated to main_window
  v3.1.0 - LGH Branded palette
"""

import os


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: ASSET PATHS
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))
ASSETS_DIR      = os.path.join(BASE_DIR, "app", "assets", "images")
LOGO_PATH       = os.path.join(ASSETS_DIR, "lghlogo.png")
CONFIG_DIR      = os.path.join(BASE_DIR, "config")
PROCEDURES_FILE = os.path.join(CONFIG_DIR, "procedures.txt")
ACCEPTANCE_FILE = os.path.join(CONFIG_DIR, "acceptance.txt")


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: SYSTEM THRESHOLDS
# Modify these values to adjust when warning states trigger.
# ═══════════════════════════════════════════════════════════════════════════════

TEMP_WARNING_THRESHOLD    = 55    # °C  — temp button turns red above this
DISK_WARNING_THRESHOLD_GB = 5.0   # GB  — disk button turns amber below this


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: LGH BRAND COLOR PALETTE
# Always reference COLORS dict — never use raw hex strings elsewhere.
# ═══════════════════════════════════════════════════════════════════════════════

COLORS = {
    # ── Deep Green (LGH Shield) ──────────────────────────────────────────────
    'success':              '#1a6b2a',
    'success_hover':        '#145522',
    'success_pressed':      '#0f3d19',

    # ── Crimson Red (LGH Crescent) ───────────────────────────────────────────
    'danger':               '#cc1414',
    'danger_hover':         '#a81010',
    'danger_pressed':       '#850d0d',

    # ── Royal Blue (LGH Banner) ──────────────────────────────────────────────
    'info':                 '#1a3fa0',
    'info_hover':           '#152f7a',
    'info_pressed':         '#0f2257',

    # ── Amber Warning ────────────────────────────────────────────────────────
    'warning':              '#e67e00',
    'warning_hover':        '#b86500',
    'warning_bg':           '#fef5e7',

    # ── Text ─────────────────────────────────────────────────────────────────
    'text_primary':         '#1a1a1a',
    'text_secondary':       '#555555',
    'text_light':           '#f5f5f5',
    'text_muted':           '#888888',

    # ── Backgrounds ──────────────────────────────────────────────────────────
    'background':           '#f0f2f5',
    'background_dark':      '#1e2d3d',
    'background_card':      '#ffffff',
    'border':               '#c8cfd8',
    'border_dark':          '#34495e',

    # ── Component-specific ───────────────────────────────────────────────────
    'preview_bg':           '#0d1117',   # Near-black — camera feed background
    'preview_border':       '#2c5f7a',   # Blue-grey bezel inner border
    'preview_border_outer': '#0a1929',   # Darker outer border for depth effect
    # TOP BAR background — lighter slate (was near-black #1e2d3d in v4.0)
    'status_bar_bg':        '#4a6278',
    # NAV BAR background — remains dark so green buttons pop
    'nav_bar_bg':           '#1e2d3d',
    'status_bar_text':      '#ecf0f1',
    'status_ready':         '#1a6b2a',
    'status_recording':     '#cc1414',

    # ── Top Bar: Temperature button ───────────────────────────────────────────
    'temp_normal':          '#1a3fa0',   # Royal blue  — normal operating temp
    'temp_normal_hover':    '#152f7a',
    'temp_warning':         '#cc1414',   # Crimson red — above TEMP_WARNING_THRESHOLD

    # ── Top Bar: Disk space button ────────────────────────────────────────────
    'disk_normal':          '#0e7490',   # Teal   — adequate storage
    'disk_normal_hover':    '#0c5f73',
    'disk_warning':         '#e67e00',   # Amber  — below DISK_WARNING_THRESHOLD_GB

    # ── Top Bar: VRM logo button ──────────────────────────────────────────────
    'vrm_logo_bg':          '#2c3e50',
    'vrm_logo_highlight':   '#3d5166',
    'vrm_logo_shadow':      '#1a252f',
    'vrm_logo_text':        '#ecf0f1',

    # ── Status Popup card ─────────────────────────────────────────────────────
    'popup_bg':             '#1a2535',
    'popup_text':           '#ecf0f1',
    'popup_text_dim':       '#a0aab4',
    # Popup header colours (normal / warning variants)
    'popup_header_temp':    '#1a3fa0',   # Blue  — temp ok
    'popup_header_temp_w':  '#cc1414',   # Red   — temp warning
    'popup_header_disk':    '#0e7490',   # Teal  — disk ok
    'popup_header_disk_w':  '#e67e00',   # Amber — disk warning
}


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: SPACING SCALE  (8px grid)
# ═══════════════════════════════════════════════════════════════════════════════

SPACING = {
    'xs':  4,
    'sm':  8,
    'md':  16,
    'lg':  24,
    'xl':  32,
    'xxl': 48,
}


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: LAYOUT SIZES
#
# Screen: 1024 x 600
#   Top bar:      70px
#   Nav bar:      90px
#   Content area: 440px  →  margins 16+8=24px  →  inner 416px
#
# Controls area (416 - 65 info row - 8 spacing = 343px):
#   Right col:  status_label 42px + 6px gap + preview 295px = 343px
#   Left col:   timer 62px + 6px gap + record_btn 275px = 343px (recording)
#               timer hidden + record_btn 275px (idle, centred with stretch)
# ═══════════════════════════════════════════════════════════════════════════════

SIZES = {
    # ── Top Bar ──────────────────────────────────────────────────────────────
    'top_bar_height':           70,
    'vrm_logo_button':          (64, 56),    # "VR / MS" stacked text
    'temp_disk_button':         (80, 56),    # wider to fit "TEMP" / " SSD" text
    'close_button':             (55, 55),    # Red circle ✕

    # ── Navigation Bar ───────────────────────────────────────────────────────
    'nav_bar_height':           90,
    'nav_button_height':        74,

    # ── Recording Screen — Info Row ──────────────────────────────────────────
    'info_button':              (220, 65),   # Increased height + font
    'info_row_height':          72,          # Fixed height shared by info_row AND timer_label
                                             # so layout never shifts between idle/recording

    # ── Recording Screen — Controls (two-column layout) ──────────────────────
    'preview':                  (430, 315),  # RIGHT column: increased height
    'record_button':            (490, 275),  # LEFT column: record button

    # ── Font Sizes ───────────────────────────────────────────────────────────
    'font_top_bar_clock':       34,          # Centred date/time (increased)
    'font_top_bar_icon':        17,          # VRM / TEMP / SSD labels

    'font_timer':               52,          # Recording counter above button
    'font_status':              26,          # "Ready to Record" / "● RECORDING"
    'font_info_display':        20,
    'font_label':               18,

    'font_button_primary':      34,          # START / STOP RECORDING
    'font_button_secondary':    22,          # Add Info, Clear (increased)
    'font_nav_button':          20,          # REC / LIB / SET (increased)

    # Popup card
    'font_popup_title':         22,          # Popup header title text
    'font_popup':               21,          # Popup body primary line
    'font_popup_small':         18,          # Popup body secondary lines
    'popup_width':              500,
    'popup_min_height':         220,

    # Misc
    'font_storage':             16,
    'logo_size':                (48, 48),
    'about_button':             (48, 48),
}


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: TIMING CONSTANTS  (all values in milliseconds)
# ═══════════════════════════════════════════════════════════════════════════════

TIMINGS = {
    'storage_check':        30000,   # 30s background SSD space check
    'timer_update':         100,     # 100ms recording elapsed-time tick
    'clock_update':         1000,    # 1s   top bar clock refresh
    'dot_blink':            600,     # 600ms recording indicator blink
    'preview_throttle':     3,       # frames to skip between preview updates

    'popup_dismiss':        4000,    # 4s   auto-dismiss popup card
    'status_clear':         3000,    # 3s   clear confirmation message

    'vrm_expand_show':      2000,    # 2s   VRM name expand stays visible
    'flash_interval':       500,     # 500ms warning button flash cycle

    'splash_duration':      3000,
}


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: STYLESHEET GENERATORS — GENERAL BUTTONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_button_style(bg, hover, pressed, font_size=14, radius=10):
    """
    Generate standard QPushButton QSS.

    Args:
        bg, hover, pressed (str): Hex colour for each state
        font_size (int): Pixels
        radius (int): Border-radius pixels

    Returns:
        str: Complete QSS string
    """
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {COLORS['text_light']};
            border: none;
            border-radius: {radius}px;
            font-size: {font_size}px;
            font-weight: bold;
            letter-spacing: 0.5px;
        }}
        QPushButton:hover    {{ background-color: {hover}; }}
        QPushButton:pressed  {{ background-color: {pressed}; }}
        QPushButton:disabled {{
            background-color: {COLORS['text_muted']};
            color: {COLORS['border']};
        }}
    """


def get_record_button_style(is_recording=False):
    """
    QSS for the START / STOP recording button.

    Args:
        is_recording (bool): True → red STOP style, False → green START style

    Returns:
        str: QSS string
    """
    if is_recording:
        return get_button_style(
            COLORS['danger'], COLORS['danger_hover'], COLORS['danger_pressed'],
            font_size=SIZES['font_button_primary'], radius=14,
        )
    return get_button_style(
        COLORS['success'], COLORS['success_hover'], COLORS['success_pressed'],
        font_size=SIZES['font_button_primary'], radius=14,
    )


def get_info_button_style(has_info=False):
    """
    QSS for the Add Info / Edit Info button.

    Args:
        has_info (bool): True → amber Edit style, False → blue Add style

    Returns:
        str: QSS string
    """
    if has_info:
        return get_button_style(
            COLORS['warning'], COLORS['warning_hover'], COLORS['warning_hover'],
            font_size=SIZES['font_button_secondary'], radius=8,
        )
    return get_button_style(
        COLORS['info'], COLORS['info_hover'], COLORS['info_pressed'],
        font_size=SIZES['font_button_secondary'], radius=8,
    )


def get_storage_bar_style(level='ok'):
    """
    QSS for storage / progress bar inside popup cards.

    Args:
        level (str): 'ok' green | 'low' amber | 'critical' red

    Returns:
        str: QSS string
    """
    chunk = {
        'ok':       COLORS['success'],
        'low':      COLORS['warning'],
        'critical': COLORS['danger'],
    }.get(level, COLORS['success'])

    return f"""
        QProgressBar {{
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 6px;
            background-color: rgba(255,255,255,0.10);
            text-align: center;
            color: {COLORS['text_light']};
            font-size: {SIZES['font_popup_small']}px;
            font-weight: bold;
            height: 26px;
        }}
        QProgressBar::chunk {{
            background-color: {chunk};
            border-radius: 5px;
        }}
    """


def get_about_button_style():
    """QSS for the circular ℹ about button."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['text_muted']};
            border: 1px solid {COLORS['border']};
            border-radius: 18px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLORS['info']};
            color: {COLORS['text_light']};
            border-color: {COLORS['info']};
        }}
    """


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: STYLESHEET GENERATORS — TOP BAR ICON BUTTONS
# NOTE: NO emoji — Linux Raspberry Pi OS has no emoji font.
#       All labels use plain ASCII / Unicode characters.
# ═══════════════════════════════════════════════════════════════════════════════

def get_vrm_logo_style():
    """
    QSS for the VRM logo button (top-left, 3D press effect via border shading).

    Returns:
        str: QSS string
    """
    bg     = COLORS['vrm_logo_bg']
    hi     = COLORS['vrm_logo_highlight']
    shadow = COLORS['vrm_logo_shadow']
    txt    = COLORS['vrm_logo_text']
    fsz    = SIZES['font_top_bar_icon']
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {txt};
            border-top:    2px solid {hi};
            border-left:   2px solid {hi};
            border-bottom: 2px solid {shadow};
            border-right:  2px solid {shadow};
            border-radius: 6px;
            font-size: {fsz}px;
            font-weight: bold;
        }}
        QPushButton:hover   {{ background-color: {hi}; }}
        QPushButton:pressed {{
            background-color: {shadow};
            border-top:    2px solid {shadow};
            border-left:   2px solid {shadow};
            border-bottom: 2px solid {hi};
            border-right:  2px solid {hi};
        }}
    """


def get_temp_button_style(is_warning=False):
    """
    QSS for the temperature icon button.

    Args:
        is_warning (bool): False → blue (normal), True → red (high temp)

    Returns:
        str: QSS string
    """
    bg    = COLORS['temp_warning']    if is_warning else COLORS['temp_normal']
    hover = COLORS['danger_hover']    if is_warning else COLORS['temp_normal_hover']
    fsz   = SIZES['font_top_bar_icon']
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {COLORS['text_light']};
            border-top:    2px solid rgba(255,255,255,0.30);
            border-left:   2px solid rgba(255,255,255,0.30);
            border-bottom: 2px solid rgba(0,0,0,0.35);
            border-right:  2px solid rgba(0,0,0,0.35);
            border-radius: 6px;
            font-size: {fsz}px;
            font-weight: bold;
        }}
        QPushButton:hover   {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {COLORS['danger_pressed']}; }}
    """


def get_disk_button_style(is_warning=False):
    """
    QSS for the disk space icon button.

    Args:
        is_warning (bool): False → teal (normal), True → amber (low space)

    Returns:
        str: QSS string
    """
    bg    = COLORS['disk_warning']      if is_warning else COLORS['disk_normal']
    hover = COLORS['warning_hover']     if is_warning else COLORS['disk_normal_hover']
    fsz   = SIZES['font_top_bar_icon']
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {COLORS['text_light']};
            border-top:    2px solid rgba(255,255,255,0.30);
            border-left:   2px solid rgba(255,255,255,0.30);
            border-bottom: 2px solid rgba(0,0,0,0.35);
            border-right:  2px solid rgba(0,0,0,0.35);
            border-radius: 6px;
            font-size: {fsz}px;
            font-weight: bold;
        }}
        QPushButton:hover   {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {COLORS['danger_pressed']}; }}
    """


def get_nav_button_style():
    """
    QSS for the bottom navigation bar buttons (REC / LIB / SET).
    LGH green on dark nav bar for high visibility.

    Returns:
        str: QSS string
    """
    return f"""
        QPushButton {{
            background-color: {COLORS['success']};
            color: {COLORS['text_light']};
            border-top:    2px solid rgba(255,255,255,0.28);
            border-left:   2px solid rgba(255,255,255,0.28);
            border-bottom: 2px solid rgba(0,0,0,0.38);
            border-right:  2px solid rgba(0,0,0,0.38);
            border-radius: 8px;
            font-size: {SIZES['font_nav_button']}px;
            font-weight: bold;
        }}
        QPushButton:pressed {{ background-color: {COLORS['success_pressed']}; }}
        QPushButton:hover   {{ background-color: {COLORS['success_hover']}; }}
    """


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: PROCEDURE LIST HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def load_procedures():
    """Load procedures from config/procedures.txt (skips comments/blanks)."""
    procedures = []
    try:
        if os.path.exists(PROCEDURES_FILE):
            with open(PROCEDURES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        procedures.append(line)
    except Exception:
        pass
    if not procedures:
        procedures = ["Phacoemulsification (Phaco)", "Other (Specify in Notes)"]
    return procedures


def save_procedures(procedures):
    """Save updated procedure list to config/procedures.txt."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(PROCEDURES_FILE, 'w', encoding='utf-8') as f:
            f.write("# VRMS - Video Recording Management System\n")
            f.write("# Lahore General Hospital - Eye Department\n")
            f.write("# Managed by: Department Head via Settings\n#\n")
            for proc in procedures:
                if proc.strip():
                    f.write(f"{proc.strip()}\n")
        return True, None
    except Exception as e:
        return False, str(e)


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: DISCLAIMER ACCEPTANCE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def is_disclaimer_accepted():
    """Check if disclaimer was previously accepted."""
    try:
        if os.path.exists(ACCEPTANCE_FILE):
            with open(ACCEPTANCE_FILE, 'r') as f:
                return 'DISCLAIMER_ACCEPTED=True' in f.read()
    except Exception:
        pass
    return False


def save_acceptance():
    """Write acceptance record to config/acceptance.txt."""
    from datetime import datetime
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        now = datetime.now()
        with open(ACCEPTANCE_FILE, 'w') as f:
            f.write("DISCLAIMER_ACCEPTED=True\n")
            f.write(f"ACCEPTED_DATE={now.strftime('%Y-%m-%d')}\n")
            f.write(f"ACCEPTED_TIME={now.strftime('%H:%M:%S')}\n")
            f.write("APP_VERSION=4.1.0\n")
            f.write("HOSPITAL=Lahore General Hospital\n")
            f.write("DEPARTMENT=Eye Department\n")
        return True, None
    except Exception as e:
        return False, str(e)


def get_acceptance_date():
    """Return acceptance date string for About dialog."""
    try:
        if os.path.exists(ACCEPTANCE_FILE):
            with open(ACCEPTANCE_FILE, 'r') as f:
                for line in f:
                    if line.startswith('ACCEPTED_DATE='):
                        return line.split('=')[1].strip()
    except Exception:
        pass
    return 'Not recorded'



# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: KEYBOARD THEMES
# Three themes selectable from Settings screen.
# Each theme is a dict passed to OnScreenKeyboard(theme=KEYBOARD_THEMES['dark'])
# ═══════════════════════════════════════════════════════════════════════════════

KEYBOARD_THEMES = {
    # ── Dark (default) — iPhone/Android dark mode style ──────────────────────
    'dark': {
        'name':         'Dark',
        'kb_bg':        '#1a1a1a',   # keyboard background
        'key_bg':       '#3a3a3c',   # normal key background
        'key_bg_press': '#222224',   # key background when pressed
        'key_special':  '#2c2c2e',   # special key (space, backspace, shift)
        'key_action':   '#1a3fa0',   # action key (done, numbers toggle)
        'key_text':     '#ffffff',   # key label text
        'border_hi':    'rgba(255,255,255,0.25)',  # 3D light edge
        'border_lo':    'rgba(0,0,0,0.60)',         # 3D dark edge
    },
    # ── Light — standard mobile light theme ──────────────────────────────────
    'light': {
        'name':         'Light',
        'kb_bg':        '#d1d5db',
        'key_bg':       '#ffffff',
        'key_bg_press': '#c5c9ce',
        'key_special':  '#adb5bd',
        'key_action':   '#1a3fa0',
        'key_text':     '#1a1a1a',
        'border_hi':    'rgba(255,255,255,0.80)',
        'border_lo':    'rgba(0,0,0,0.25)',
    },
    # ── LGH Brand — hospital colour scheme ───────────────────────────────────
    'lgh': {
        'name':         'LGH Brand',
        'kb_bg':        '#1e2d3d',
        'key_bg':       '#2c3e50',
        'key_bg_press': '#1a252f',
        'key_special':  '#243342',
        'key_action':   '#1a6b2a',   # LGH green
        'key_text':     '#ecf0f1',
        'border_hi':    'rgba(255,255,255,0.20)',
        'border_lo':    'rgba(0,0,0,0.50)',
    },
}

# Default theme name — changeable via Settings
KEYBOARD_DEFAULT_THEME = 'dark'

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK: MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    'COLORS', 'SPACING', 'SIZES', 'TIMINGS',
    'TEMP_WARNING_THRESHOLD', 'DISK_WARNING_THRESHOLD_GB',
    'LOGO_PATH', 'PROCEDURES_FILE', 'ACCEPTANCE_FILE',
    'get_button_style', 'get_record_button_style',
    'get_info_button_style', 'get_storage_bar_style', 'get_about_button_style',
    'get_vrm_logo_style', 'get_temp_button_style', 'get_disk_button_style',
    'get_nav_button_style',
    'load_procedures', 'save_procedures',
    'is_disclaimer_accepted', 'save_acceptance', 'get_acceptance_date',
    'KEYBOARD_THEMES', 'KEYBOARD_DEFAULT_THEME',
]
