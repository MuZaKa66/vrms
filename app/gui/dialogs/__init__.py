"""
GUI Dialogs Package
Lahore General Hospital - OT Video Recording System

Contains:
- splash_screen.py      : Startup splash shown every launch
- disclaimer_dialog.py  : First-launch disclaimer + acceptance
- about_dialog.py       : App info, branding, credits
- close_confirm_dialog.py: App exit confirmation handler

Author: ZKB
Special Thanks: Dr. Farqaleet
"""

from .splash_screen import SplashScreen
from .disclaimer_dialog import DisclaimerDialog
from .about_dialog import AboutDialog
from .close_confirm_dialog import CloseConfirmDialog

__all__ = [
    'SplashScreen',
    'DisclaimerDialog',
    'AboutDialog',
    'CloseConfirmDialog',
]
