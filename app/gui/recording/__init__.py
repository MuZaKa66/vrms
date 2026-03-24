"""
Recording Screen Package

Modularized recording interface for OT Video System.
Refactored from single 1400+ line file into maintainable components.

Package Structure:
- recording_screen.py: Main controller orchestrating all components
- design_constants.py: UI design system (colors, sizes, spacing)
- ui_builder.py: UI component creation and layout
- preview_handler.py: Video preview rendering and updates
- recording_controller_wrapper.py: Recording state management
- metadata_handler.py: Patient/procedure info management

Author: OT Video Dev Team
Date: February 16, 2026
Version: 2.0.0 (Refactored)
"""

from .recording_screen import RecordingScreen

__all__ = ['RecordingScreen']
