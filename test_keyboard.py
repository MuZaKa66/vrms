"""
Standalone keyboard test — /opt/vrms1/test_keyboard.py
Run: python3 test_keyboard.py
Press Escape or tap EXIT button to quit.
"""
import sys
sys.path.insert(0, '/opt/vrms1')

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QPushButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

app = QApplication(sys.argv)
app.setStyle("Fusion")

window = QWidget()
window.setWindowTitle("Keyboard Test")
window.setGeometry(0, 0, 1024, 370)
window.setStyleSheet("background: #f0f2f5;")

layout = QVBoxLayout(window)
layout.setSpacing(16)
layout.setContentsMargins(30, 20, 30, 10)

# Title + exit row
top = QHBoxLayout()
title = QLabel("Touch Keyboard Test")
title.setFont(QFont("Arial", 20, QFont.Bold))
top.addWidget(title)
top.addStretch()
exit_btn = QPushButton("EXIT")
exit_btn.setFixedSize(100, 45)
exit_btn.setFont(QFont("Arial", 14, QFont.Bold))
exit_btn.setStyleSheet("background:#cc1414;color:white;border:none;border-radius:6px;")
exit_btn.clicked.connect(app.quit)
top.addWidget(exit_btn)
layout.addLayout(top)

# Instructions
info = QLabel("Tap a field → keyboard appears.  Type.  Wait 5s → hides.  Tap again → reappears.")
info.setFont(QFont("Arial", 12))
layout.addWidget(info)

# Field 1
layout.addWidget(QLabel("Patient Name:"))
field1 = QLineEdit()
field1.setPlaceholderText("Tap here...")
field1.setFont(QFont("Arial", 16))
field1.setFixedHeight(52)
field1.setStyleSheet("border:2px solid #1a3fa0;border-radius:6px;padding:8px;")
layout.addWidget(field1)

# Field 2
layout.addWidget(QLabel("Procedure:"))
field2 = QLineEdit()
field2.setPlaceholderText("Tap here...")
field2.setFont(QFont("Arial", 16))
field2.setFixedHeight(52)
field2.setStyleSheet("border:2px solid #1a3fa0;border-radius:6px;padding:8px;")
layout.addWidget(field2)

# Status
status = QLabel("Status: tap a field to start")
status.setFont(QFont("Arial", 12))
status.setStyleSheet("color:#555555;")
layout.addWidget(status)

# Keyboard shortcut to exit
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
QShortcut(QKeySequence("Escape"), window, activated=app.quit)

window.show()

# Keyboard
from app.widgets.touch_keyboard import TouchKeyboard
kb = TouchKeyboard(parent=None, screen_w=1024, screen_h=600, kb_height=220)
kb.key_pressed.connect(lambda a: status.setText(f"Last key: {a}  |  Field1: {field1.text()}"))
kb.attach_to_app(app)

print("Ready. Tap a text field. Press Escape or EXIT to quit.")
sys.exit(app.exec_())
