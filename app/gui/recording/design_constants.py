"""
Design Constants - LGH Branded UI Design System

Colors extracted from Lahore General Hospital logo:
  - Deep Green  (#1a6b2a) - Shield border
  - Crimson Red (#cc1414) - Crescent moon  
  - Royal Blue  (#1a3fa0) - Hospital banner

Author: ZKB
Special Thanks: Dr. Farqaleet
Hospital: Lahore General Hospital - Eye Department
Date: February 17, 2026
Version: 2.1.0 (LGH Branded)
"""

import os

# ═══════════════════════════════════════════════════════════════════════════
# ASSET PATHS
# ═══════════════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))
ASSETS_DIR    = os.path.join(BASE_DIR, "app", "assets", "images")
LOGO_PATH     = os.path.join(ASSETS_DIR, "lghlogo.png")
CONFIG_DIR    = os.path.join(BASE_DIR, "config")
PROCEDURES_FILE = os.path.join(CONFIG_DIR, "procedures.txt")
ACCEPTANCE_FILE = os.path.join(CONFIG_DIR, "acceptance.txt")

# ═══════════════════════════════════════════════════════════════════════════
# LGH BRAND COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════

COLORS = {
    # Deep Green (LGH Shield)
    'success':          '#1a6b2a',
    'success_hover':    '#145522',
    'success_pressed':  '#0f3d19',

    # Crimson Red (LGH Crescent)
    'danger':           '#cc1414',
    'danger_hover':     '#a81010',
    'danger_pressed':   '#850d0d',

    # Royal Blue (LGH Banner)
    'info':             '#1a3fa0',
    'info_hover':       '#152f7a',
    'info_pressed':     '#0f2257',

    # Amber Warning
    'warning':          '#e67e00',
    'warning_hover':    '#b86500',
    'warning_bg':       '#fef5e7',

    # Text
    'text_primary':     '#1a1a1a',
    'text_secondary':   '#555555',
    'text_light':       '#f5f5f5',
    'text_muted':       '#888888',

    # Backgrounds
    'background':       '#f0f2f5',
    'background_dark':  '#1e2d3d',
    'background_card':  '#ffffff',
    'border':           '#c8cfd8',
    'border_dark':      '#34495e',

    # Components
    'preview_bg':       '#1a1a2e',
    'status_bar_bg':    '#1e2d3d',
    'status_bar_text':  '#ecf0f1',
    'status_ready':     '#1a6b2a',
    'status_recording': '#cc1414',
}

# ═══════════════════════════════════════════════════════════════════════════
# SPACING SCALE (8px grid)
# ═══════════════════════════════════════════════════════════════════════════

SPACING = {
    'xs': 4, 'sm': 8, 'md': 16,
    'lg': 24, 'xl': 32, 'xxl': 48,
}

# ═══════════════════════════════════════════════════════════════════════════
# SIZES - Optimized for 7" touchscreen + gloved hands at 2-3m
# ═══════════════════════════════════════════════════════════════════════════

SIZES = {
    'preview':              (280, 210),
    'record_button':        (380, 160),
    'info_button':          (180, 55),
    'status_bar_height':    44,
    'logo_size':            (32, 32),
    'about_button':         (36, 36),

    # Fonts - readable at 2-3 meters
    'font_timer':           52,
    'font_status':          16,
    'font_button_primary':  26,
    'font_button_secondary':13,
    'font_label':           13,
    'font_info_display':    14,
    'font_clock':           15,
    'font_storage':         12,
}

# ═══════════════════════════════════════════════════════════════════════════
# TIMING CONSTANTS (milliseconds)
# ═══════════════════════════════════════════════════════════════════════════

TIMINGS = {
    'storage_check':    30000,
    'timer_update':     100,
    'clock_update':     1000,
    'dot_blink':        600,
    'status_clear':     3000,
    'preview_throttle': 3,
    'splash_duration':  3000,
}

# ═══════════════════════════════════════════════════════════════════════════
# STYLESHEET GENERATORS
# ═══════════════════════════════════════════════════════════════════════════

def get_button_style(bg, hover, pressed, font_size=14, radius=10):
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
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; }}
        QPushButton:disabled {{
            background-color: {COLORS['text_muted']};
            color: {COLORS['border']};
        }}
    """

def get_record_button_style(is_recording=False):
    if is_recording:
        return get_button_style(
            COLORS['danger'], COLORS['danger_hover'], COLORS['danger_pressed'],
            font_size=SIZES['font_button_primary'], radius=12)
    return get_button_style(
        COLORS['success'], COLORS['success_hover'], COLORS['success_pressed'],
        font_size=SIZES['font_button_primary'], radius=12)

def get_info_button_style(has_info=False):
    if has_info:
        return get_button_style(
            COLORS['warning'], COLORS['warning_hover'], COLORS['warning_hover'],
            font_size=SIZES['font_button_secondary'], radius=8)
    return get_button_style(
        COLORS['info'], COLORS['info_hover'], COLORS['info_pressed'],
        font_size=SIZES['font_button_secondary'], radius=8)

def get_storage_bar_style(level='ok'):
    chunk = {'ok': COLORS['success'], 'low': COLORS['warning'],
             'critical': COLORS['danger']}.get(level, COLORS['success'])
    return f"""
        QProgressBar {{
            border: none; border-radius: 4px;
            background-color: rgba(255,255,255,0.15);
            text-align: center;
            color: {COLORS['status_bar_text']};
            font-size: {SIZES['font_storage']}px;
            font-weight: bold; height: 20px;
        }}
        QProgressBar::chunk {{ background-color: {chunk}; border-radius: 4px; }}
    """

def get_about_button_style():
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['text_muted']};
            border: 1px solid {COLORS['border']};
            border-radius: 18px;
            font-size: 16px; font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLORS['info']};
            color: {COLORS['text_light']};
            border-color: {COLORS['info']};
        }}
    """

# ═══════════════════════════════════════════════════════════════════════════
# PROCEDURE LIST HELPERS
# ═══════════════════════════════════════════════════════════════════════════

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
            f.write("# OT Video Recording System - Procedure List\n")
            f.write("# Lahore General Hospital - Eye Department\n")
            f.write("# Managed by: Department Head via Settings\n#\n")
            for proc in procedures:
                if proc.strip():
                    f.write(f"{proc.strip()}\n")
        return True, None
    except Exception as e:
        return False, str(e)

# ═══════════════════════════════════════════════════════════════════════════
# DISCLAIMER ACCEPTANCE HELPERS
# ═══════════════════════════════════════════════════════════════════════════

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
            f.write(f"DISCLAIMER_ACCEPTED=True\n")
            f.write(f"ACCEPTED_DATE={now.strftime('%Y-%m-%d')}\n")
            f.write(f"ACCEPTED_TIME={now.strftime('%H:%M:%S')}\n")
            f.write(f"APP_VERSION=2.1.0\n")
            f.write(f"HOSPITAL=Lahore General Hospital\n")
            f.write(f"DEPARTMENT=Eye Department\n")
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

__all__ = [
    'COLORS', 'SPACING', 'SIZES', 'TIMINGS',
    'LOGO_PATH', 'PROCEDURES_FILE', 'ACCEPTANCE_FILE',
    'get_button_style', 'get_record_button_style',
    'get_info_button_style', 'get_storage_bar_style',
    'get_about_button_style',
    'load_procedures', 'save_procedures',
    'is_disclaimer_accepted', 'save_acceptance', 'get_acceptance_date',
]
