"""
File: app/gui/widgets/on_screen_keyboard.py

Mobile-style embedded keyboard — 5 row layout, 10 columns aligned.

LAYOUT:
  Row 1:  1  2  3  4  5  6  7  8  9  0
  Row 2:  Q  W  E  R  T  Y  U  I  O  P
  Row 3:  A  S  D  F  G  H  J  K  L  '
  Row 4: [CAPS] Z  X  C  V  B  N  M [⌫]
  Row 5: [123] [,] [___SPACE___] [.] [↵]

All rows 10-column aligned. CAPS and ⌫ are double-width.
Space bar fills centre. ↵ is double-width.

THEMES: dark (default), light, lgh — from design_constants.KEYBOARD_THEMES
3D KEYS: raised normal, sunken on press.
3D PANEL: keyboard container has gradient + raised border — looks like a
          physical panel lifted off the screen surface.

Author: OT Video Dev Team / ZKB
Date: April 9, 2026
Version: 4.3.0
Changelog:
    - v4.3.0: 3D raised panel effect on keyboard container.
              setObjectName("OnScreenKeyboard") allows QSS to target the
              outer container independently of child widgets.
              Gradient calculated from kb_bg — works for all themes.
              setAutoFillBackground(True) ensures solid opaque background.
    - v4.2.0: Bottom contentsMargin 6 -> 0. Keys flush with widget bottom.
    - v4.1.0: retainSizeWhenHidden(False). addStretch().
    - v4.0.0: Initial release.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from app.utils.logger import AppLogger
logger = AppLogger("OnScreenKeyboard")

# ── Keyboard dimensions ────────────────────────────────────────────────────────
KEY_W      = 94    # standard key width  (10 keys + 9 gaps = 10*94 + 9*4 = 976px)
KEY_H      = 45    # standard key height
KEY_WIDE   = 188   # double-width key (CAPS, ⌫, ↵)
SPACE_W    = 400   # space bar width
GAP        = 4     # gap between keys
FONT_SZ    = 22    # key label font size

# ── Letter rows ────────────────────────────────────────────────────────────────
ROW1 = [('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),
        ('6','6'),('7','7'),('8','8'),('9','9'),('0','0')]

ROW2 = [('Q','q'),('W','w'),('E','e'),('R','r'),('T','t'),
        ('Y','y'),('U','u'),('I','i'),('O','o'),('P','p')]

ROW3 = [('A','a'),('S','s'),('D','d'),('F','f'),('G','g'),
        ('H','h'),('J','j'),('K','k'),('L','l'),("'","'")]

ROW4_MID = [('Z','z'),('X','x'),('C','c'),('V','v'),('B','b'),
            ('N','n'),('M','m')]

# ── Number panel rows ──────────────────────────────────────────────────────────
NROW1 = [('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),
         ('6','6'),('7','7'),('8','8'),('9','9'),('0','0')]
NROW2 = [('-','-'),('/','/'),(':',' :'),('_','_'),('(','('),
         (')',')'),('&','&'),('@','@'),('"','"'),('?','?')]
NROW3 = [('!','!'),("'","'"),('+','+'),(';',';'),(',',','),
         ('.','.'),('"','"'),('=','='),('#','#'),('%','%')]


class OnScreenKeyboard(QWidget):
    """
    Mobile-style embedded keyboard for VRMS touchscreen.

    Signals:
        text_changed(str): text buffer changed
        enter_pressed():   OK/Enter tapped
        cancelled():       Cancel tapped (kept for API compatibility)
    """

    text_changed  = pyqtSignal(str)
    enter_pressed = pyqtSignal()
    cancelled     = pyqtSignal()

    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)       # embedded — never top-level
        self.setAutoFillBackground(True)     # paint solid bg — covers content behind keyboard
        self.setObjectName("OnScreenKeyboard")
        self.setAttribute(Qt.WA_StyledBackground, True)  # allows QSS to target this widget only

        # ── Load theme ─────────────────────────────────────────────────────────
        if theme is None:
            try:
                from app.gui.recording.design_constants import (
                    KEYBOARD_THEMES, KEYBOARD_DEFAULT_THEME
                )
                theme = KEYBOARD_THEMES[KEYBOARD_DEFAULT_THEME]
            except Exception:
                theme = {
                    'kb_bg':        '#1a1a1a',
                    'key_bg':       '#3a3a3c',
                    'key_bg_press': '#222224',
                    'key_special':  '#2c2c2e',
                    'key_action':   '#1a3fa0',
                    'key_text':     '#ffffff',
                    'border_hi':    'rgba(255,255,255,0.25)',
                    'border_lo':    'rgba(0,0,0,0.60)',
                }
        self._t = theme

        # ── Calculate lighter gradient stop from kb_bg ─────────────────────────
        # Adds +20 to each RGB channel for the top of the gradient.
        # Gives the keyboard a subtle depth — lighter at top, darker at bottom.
        try:
            hx = theme['kb_bg'].lstrip('#')
            r, g, b = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
            lighter = f'#{min(255,r+20):02x}{min(255,g+20):02x}{min(255,b+20):02x}'
        except Exception:
            lighter = theme['kb_bg']   # fallback: flat colour if parse fails

        hi = theme['border_hi']
        lo = theme['border_lo']

        # ── Stylesheet ─────────────────────────────────────────────────────────
        # QWidget rule:            sets background for ALL child widgets (key gaps etc.)
        # #OnScreenKeyboard rule:  targets ONLY the outer container via objectName.
        #                          Gradient + raised 3D border give a physical panel feel.
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['kb_bg']};
            }}
            #OnScreenKeyboard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {lighter},
                    stop:1 {theme['kb_bg']}
                );
                border-top:    3px solid {hi};
                border-left:   3px solid {hi};
                border-bottom: 3px solid {lo};
                border-right:  3px solid {lo};
                border-radius: 6px;
            }}
        """)

        self.text       = ""
        self._shift     = 0      # 0=lower 1=shift-once 2=caps
        self._panel     = 'letters'
        self._shift_btn = None
        self._ltr_btns  = []     # letter buttons for case update

        vl = QVBoxLayout(self)
        # ── bottom margin = 0: keys flush with widget bottom edge ──────────────
        vl.setContentsMargins(6, 6, 6, 0)
        vl.setSpacing(GAP)

        self._lw = self._build_letters()
        self._nw = self._build_numbers()

        # ── Panels must NOT reserve space when hidden ──────────────────────────
        for panel in (self._lw, self._nw):
            sp = panel.sizePolicy()
            sp.setRetainSizeWhenHidden(False)
            panel.setSizePolicy(sp)

        vl.addWidget(self._lw)
        vl.addWidget(self._nw)
        vl.addStretch()          # absorbs any surplus height — rows never stretch
        self._nw.setVisible(False)

        logger.debug("OnScreenKeyboard v4.3 initialized")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: PANEL BUILDERS
    # ─────────────────────────────────────────────────────────────────────────

    def _build_letters(self):
        """Letters panel — 5 rows, 10-column aligned."""
        w = QWidget(self)
        w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(GAP)
        vl.addLayout(self._std_row(ROW1))
        vl.addLayout(self._std_row(ROW2))
        vl.addLayout(self._std_row(ROW3))
        vl.addLayout(self._row4())
        vl.addLayout(self._row5())
        return w

    def _build_numbers(self):
        """Numbers/symbols panel."""
        w = QWidget(self)
        w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(GAP)
        vl.addLayout(self._std_row(NROW1))
        vl.addLayout(self._std_row(NROW2))
        vl.addLayout(self._std_row(NROW3))

        r4 = QHBoxLayout()
        r4.setContentsMargins(0, 0, 0, 0)
        r4.setSpacing(GAP)
        r4.addWidget(self._key('ABC', 'LETTERS', 'special', KEY_WIDE, KEY_H))
        r4.addWidget(self._key('___', 'SPACE',   'special', SPACE_W,  KEY_H))
        r4.addWidget(self._key('⌫',  'BACKSPACE','special', KEY_WIDE, KEY_H))
        vl.addLayout(r4)
        vl.addLayout(self._row5())
        return w

    def _std_row(self, keys):
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(GAP)
        for label, action in keys:
            hl.addWidget(self._key(label, action, 'normal', KEY_W, KEY_H))
        return hl

    def _row4(self):
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(GAP)
        hl.addWidget(self._key('CAPS', 'SHIFT',    'special', KEY_WIDE, KEY_H))
        for label, action in ROW4_MID:
            hl.addWidget(self._key(label, action,  'normal',  KEY_W,    KEY_H))
        hl.addWidget(self._key('⌫',   'BACKSPACE', 'special', KEY_WIDE, KEY_H))
        return hl

    def _row5(self):
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(GAP)
        hl.addWidget(self._key('123', 'NUMBERS', 'special', KEY_WIDE, KEY_H))
        hl.addWidget(self._key(',',   ',',       'normal',  KEY_W,    KEY_H))
        hl.addWidget(self._key('',    'SPACE',   'special', SPACE_W,  KEY_H))
        hl.addWidget(self._key('.',   '.',       'normal',  KEY_W,    KEY_H))
        hl.addWidget(self._key('↵',   'DONE',    'action',  KEY_WIDE, KEY_H))
        return hl

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: KEY FACTORY
    # ─────────────────────────────────────────────────────────────────────────

    def _key(self, label, action, ktype, w, h):
        t = self._t
        if ktype == 'action':    bg = t['key_action']
        elif ktype == 'special': bg = t['key_special']
        else:                    bg = t['key_bg']

        hi = t['border_hi']
        lo = t['border_lo']

        try:
            hx = bg.lstrip('#')
            r, g, b2 = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
            pbg = f'#{max(0,r-30):02x}{max(0,g-30):02x}{max(0,b2-30):02x}'
        except Exception:
            pbg = bg

        qss = f"""
            QPushButton {{
                background-color: {bg};
                color: {t['key_text']};
                border-top:    2px solid {hi};
                border-left:   2px solid {hi};
                border-bottom: 2px solid {lo};
                border-right:  2px solid {lo};
                border-radius: 5px;
                font-size: {FONT_SZ}px;
                font-weight: bold;
            }}
            QPushButton:pressed {{
                background-color: {pbg};
                border-top:    2px solid {lo};
                border-left:   2px solid {lo};
                border-bottom: 2px solid {hi};
                border-right:  2px solid {hi};
            }}
        """

        btn = QPushButton(label)
        btn.setFixedSize(w, h)
        btn.setFont(QFont("Arial", FONT_SZ, QFont.Bold))
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setStyleSheet(qss)
        btn._action     = action
        btn._normal_qss = qss
        btn._bg         = bg

        btn.clicked.connect(lambda checked, a=action: self._on_key(a))

        if ktype == 'normal' and len(action) == 1 and action.isalpha():
            self._ltr_btns.append(btn)
        if action == 'SHIFT':
            self._shift_btn = btn

        return btn

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: KEY HANDLER
    # ─────────────────────────────────────────────────────────────────────────

    def _on_key(self, action):
        if action == 'BACKSPACE':
            if self.text:
                self.text = self.text[:-1]
                self.text_changed.emit(self.text)
        elif action == 'SPACE':
            self.text += ' '
            self.text_changed.emit(self.text)
        elif action == 'DONE':
            self.enter_pressed.emit()
        elif action == 'SHIFT':
            self._toggle_shift()
        elif action == 'NUMBERS':
            self._lw.setVisible(False)
            self._nw.setVisible(True)
        elif action == 'LETTERS':
            self._nw.setVisible(False)
            self._lw.setVisible(True)
        else:
            char = action.upper() if self._shift > 0 else action.lower()
            self.text += char
            self.text_changed.emit(self.text)
            if self._shift == 1:
                self._shift = 0
                self._update_case()
                if self._shift_btn:
                    self._shift_btn.setStyleSheet(self._shift_btn._normal_qss)

    def _toggle_shift(self):
        self._shift = (self._shift + 1) % 3
        self._update_case()
        if self._shift_btn:
            if self._shift > 0:
                t = self._t
                self._shift_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['key_action']};
                        color: {t['key_text']};
                        border-top:    2px solid {t['border_hi']};
                        border-left:   2px solid {t['border_hi']};
                        border-bottom: 2px solid {t['border_lo']};
                        border-right:  2px solid {t['border_lo']};
                        border-radius: 5px;
                        font-size: {FONT_SZ}px; font-weight: bold;
                    }}
                """)
            else:
                self._shift_btn.setStyleSheet(self._shift_btn._normal_qss)

    def _update_case(self):
        upper = self._shift > 0
        for btn in self._ltr_btns:
            btn.setText(btn._action.upper() if upper else btn._action.lower())

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def set_text(self, text):   self.text = text
    def get_text(self):         return self.text
    def clear(self):            self.text = ""; self.text_changed.emit(self.text)
    def show_keyboard(self):    self.setVisible(True)
    def hide_keyboard(self):    self.setVisible(False)
    def _update_display(self):  pass
    def _cancel(self):          self.cancelled.emit()
    def _enter(self):           self.enter_pressed.emit()


__all__ = ['OnScreenKeyboard']
