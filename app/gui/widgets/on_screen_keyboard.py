"""
File: app/gui/widgets/on_screen_keyboard.py

Module Description:
    Professional on-screen keyboard for medical touchscreen environment.
    
    Features:
    - Large touch-friendly buttons (60x60px minimum)
    - QWERTY layout for familiarity
    - Number row for quick entry
    - Special medical characters (-, ., /)
    - Clear visual feedback
    - Emits text to parent widget
    
    Usage:
        keyboard = OnScreenKeyboard()
        keyboard.text_changed.connect(line_edit.setText)
        keyboard.show()

Author: OT Video Dev Team
Date: February 5, 2026
Version: 2.0.0 (Medical touchscreen optimized)
"""

from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from app.utils.logger import AppLogger

logger = AppLogger("OnScreenKeyboard")


class OnScreenKeyboard(QWidget):
    """
    Professional on-screen keyboard for touchscreen input.
    
    Signals:
        text_changed(str): Emitted when text changes
        enter_pressed(): Emitted when Enter key pressed
        cancelled(): Emitted when Cancel pressed
    
    Methods:
        set_text(text): Set current text
        get_text(): Get current text
        clear(): Clear all text
        show_keyboard(): Display keyboard
        hide_keyboard(): Hide keyboard
    
    Example:
        >>> keyboard = OnScreenKeyboard()
        >>> keyboard.text_changed.connect(my_input.setText)
        >>> keyboard.enter_pressed.connect(self.save_data)
        >>> keyboard.show_keyboard()
    """
    
    # Signals
    text_changed = pyqtSignal(str)
    enter_pressed = pyqtSignal()
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialize keyboard.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.text = ""
        self.caps_lock = False
        self.init_ui()
        
        logger.debug("On-screen keyboard initialized")
    
    def init_ui(self):
        """Initialize keyboard UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Title bar
        title_layout = QHBoxLayout()
        title_label = QLabel("Enter Text")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Text display (shows what's typed)
        self.display = QLabel("")
        self.display.setMinimumHeight(60)
        self.display.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 10px;
                font-size: 20px;
                color: black;
            }
        """)
        self.display.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.display.setWordWrap(True)
        layout.addWidget(self.display)
        
        # Keyboard grid
        grid = QGridLayout()
        grid.setSpacing(5)
        
        # Number row
        numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        for col, num in enumerate(numbers):
            self._add_key_button(grid, num, 0, col)
        
        # Letter rows (QWERTY layout)
        rows = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        ]
        
        for row_idx, row in enumerate(rows):
            for col_idx, letter in enumerate(row):
                self._add_key_button(grid, letter, row_idx + 1, col_idx)
        
        # Special characters row
        specials = ['-', '.', '/', '_', ',']
        for col, char in enumerate(specials):
            self._add_key_button(grid, char, 4, col)
        
        # Space bar (spans multiple columns)
        space_btn = self._create_button('SPACE', key_type='special')
        space_btn.clicked.connect(lambda: self._key_pressed(' '))
        grid.addWidget(space_btn, 4, 5, 1, 3)  # Spans 3 columns
        
        # Backspace button
        backspace_btn = self._create_button('⌫', key_type='special')
        backspace_btn.clicked.connect(self._backspace)
        grid.addWidget(backspace_btn, 4, 8, 1, 2)  # Spans 2 columns
        
        layout.addLayout(grid)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumSize(120, 60)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        clear_btn.clicked.connect(self.clear)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumSize(120, 60)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #7f8c8d;
            }
        """)
        cancel_btn.clicked.connect(self._cancel)
        
        # Enter/Done button
        enter_btn = QPushButton("Done")
        enter_btn.setMinimumSize(120, 60)
        enter_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        enter_btn.clicked.connect(self._enter)
        
        action_layout.addWidget(clear_btn)
        action_layout.addStretch()
        action_layout.addWidget(cancel_btn)
        action_layout.addWidget(enter_btn)
        
        layout.addLayout(action_layout)
        
        # Set window properties
        self.setWindowTitle("On-Screen Keyboard")
        self.setMinimumSize(700, 450)
    
    def _add_key_button(self, grid: QGridLayout, key: str, row: int, col: int):
        """
        Add a key button to the grid.
        
        Args:
            grid: Grid layout
            key: Key character
            row: Row position
            col: Column position
        """
        btn = self._create_button(key, key_type='letter')
        btn.clicked.connect(lambda: self._key_pressed(key))
        grid.addWidget(btn, row, col)
    
    def _create_button(self, text: str, key_type: str = 'letter') -> QPushButton:
        """
        Create a keyboard button.
        
        Args:
            text: Button text
            key_type: 'letter' or 'special'
        
        Returns:
            QPushButton: Configured button
        """
        btn = QPushButton(text)
        btn.setMinimumSize(60, 60)
        
        if key_type == 'letter':
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    font-size: 18px;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #3498db;
                    color: white;
                }
            """)
        else:  # special
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #2c3e50;
                }
            """)
        
        return btn
    
    def _key_pressed(self, key: str):
        """
        Handle key press.
        
        Args:
            key: Key that was pressed
        """
        self.text += key
        self._update_display()
        self.text_changed.emit(self.text)
        logger.debug(f"Key pressed: {key}")
    
    def _backspace(self):
        """Handle backspace."""
        if self.text:
            self.text = self.text[:-1]
            self._update_display()
            self.text_changed.emit(self.text)
            logger.debug("Backspace pressed")
    
    def _update_display(self):
        """Update display label with current text."""
        display_text = self.text if self.text else "(empty)"
        self.display.setText(display_text)
    
    def clear(self):
        """Clear all text."""
        self.text = ""
        self._update_display()
        self.text_changed.emit(self.text)
        logger.debug("Text cleared")
    
    def _enter(self):
        """Handle Enter/Done button."""
        self.enter_pressed.emit()
        logger.debug("Enter pressed")
    
    def _cancel(self):
        """Handle Cancel button."""
        self.cancelled.emit()
        logger.debug("Cancelled")
    
    def set_text(self, text: str):
        """
        Set current text.
        
        Args:
            text: Text to set
        """
        self.text = text
        self._update_display()
    
    def get_text(self) -> str:
        """
        Get current text.
        
        Returns:
            str: Current text
        """
        return self.text
    
    def show_keyboard(self):
        """Show keyboard as modal dialog."""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def hide_keyboard(self):
        """Hide keyboard."""
        self.hide()


__all__ = ['OnScreenKeyboard']
