"""
File: app/gui/metadata_dialog.py

Recording Information - Full Screen Frameless Dialog

KEY LAYOUT DECISIONS:
  - Dialog covers full 1024x600 screen, positioned via showEvent (not init_ui)
  - Keyboard is positioned ABSOLUTELY at bottom — NOT in VBoxLayout
  - This means form/buttons NEVER shift when keyboard appears/disappears
  - Keyboard just overlays the bottom portion of the screen

Version: 3.2.0
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.models.metadata import RecordingMetadata, CommonProcedures
from app.controllers.metadata_controller import MetadataController
from app.utils.logger import AppLogger

logger = AppLogger("RecordingInfoDialog")

KB_HEIGHT = 430   # keyboard height in pixels


class MetadataDialog(QDialog):

    def __init__(self, recording=None, parent=None):
        super().__init__(parent)
        self.recording     = recording
        self._active_input = None
        self.init_ui()
        logger.debug("Recording info dialog initialized")

    def showEvent(self, event):
        """Force position to 0,0 every time dialog is shown."""
        super().showEvent(event)
        self.move(0, -36)

    def init_ui(self):
        self.setWindowTitle("Add Recording Info")
        self.setFixedSize(1024, 564)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setStyleSheet("QDialog { background-color: #f0f2f5; }")

        # ── Main layout — title + form + buttons only ──────────────────
        # Keyboard is NOT in this layout — it is absolutely positioned
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(20, 12, 20, 12)

        # Title
        title = QLabel("Recording Information(VRMS)")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Two-column form grid
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        grid.addWidget(self._lbl("Patient Name:"), 0, 0)
        grid.addWidget(self._lbl("Procedure Type:"), 0, 1)

        self.patient_input = self._field("Tap to enter patient name")
        self.patient_input.mousePressEvent = \
            lambda e: self._activate(self.patient_input)
        grid.addWidget(self.patient_input, 1, 0)

        self.procedure_combo = QComboBox()
        self.procedure_combo.addItems(CommonProcedures.get_all_names())
        self.procedure_combo.setMinimumHeight(50)
        self.procedure_combo.setFont(QFont("Arial", 18))
        self.procedure_combo.setStyleSheet(
            "QComboBox{font-size:18px;padding:8px;"
            "border:2px solid #bdc3c7;border-radius:5px;background:white;}")
        grid.addWidget(self.procedure_combo, 1, 1)

        grid.addWidget(self._lbl("Consultant / Surgeon:"), 2, 0)
        grid.addWidget(self._lbl("Operating Theatre:"), 2, 1)

        self.consultant_input = self._field("Tap to enter surgeon name")
        self.consultant_input.mousePressEvent = \
            lambda e: self._activate(self.consultant_input)
        grid.addWidget(self.consultant_input, 3, 0)

        self.ot_combo = QComboBox()
        self.ot_combo.addItems(["OT 1","OT 2","OT 3","OT 4","OT 5"])
        self.ot_combo.setMinimumHeight(50)
        self.ot_combo.setFont(QFont("Arial", 18))
        self.ot_combo.setStyleSheet(
            "QComboBox{font-size:18px;padding:8px;"
            "border:2px solid #bdc3c7;border-radius:5px;background:white;}")
        grid.addWidget(self.ot_combo, 3, 1)

        layout.addLayout(grid)

        # Cancel / Save buttons — fixed below form
        btn_row = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumSize(480, 52)
        cancel_btn.setFont(QFont("Arial", 17, QFont.Bold))
        cancel_btn.setStyleSheet("""
            QPushButton{
                background:#95a5a6; color:white;
                border-top:   3px solid rgba(255,255,255,0.35);
                border-left:  3px solid rgba(255,255,255,0.35);
                border-bottom:3px solid rgba(0,0,0,0.35);
                border-right: 3px solid rgba(0,0,0,0.35);
                border-radius:8px; font-weight:bold;
            }
            QPushButton:pressed{
                background:#7f8c8d;
                border-top:   3px solid rgba(0,0,0,0.35);
                border-left:  3px solid rgba(0,0,0,0.35);
                border-bottom:3px solid rgba(255,255,255,0.35);
                border-right: 3px solid rgba(255,255,255,0.35);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(24)

        save_btn = QPushButton("Save")
        save_btn.setMinimumSize(480, 52)
        save_btn.setFont(QFont("Arial", 17, QFont.Bold))
        save_btn.setStyleSheet("""
            QPushButton{
                background:#27ae60; color:white;
                border-top:   3px solid rgba(255,255,255,0.35);
                border-left:  3px solid rgba(255,255,255,0.35);
                border-bottom:3px solid rgba(0,0,0,0.35);
                border-right: 3px solid rgba(0,0,0,0.35);
                border-radius:8px; font-weight:bold;
            }
            QPushButton:pressed{
                background:#229954;
                border-top:   3px solid rgba(0,0,0,0.35);
                border-left:  3px solid rgba(0,0,0,0.35);
                border-bottom:3px solid rgba(255,255,255,0.35);
                border-right: 3px solid rgba(255,255,255,0.35);
            }
        """)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)
        layout.addStretch()

        # ── Keyboard — absolutely positioned at bottom ─────────────────
        # NOT in the VBoxLayout — this prevents ANY layout shift when shown
        self._kb_frame = QFrame(self)
        self._kb_frame.setFrameShape(QFrame.NoFrame)
        self._kb_frame.setGeometry(0, 564 - 260, 1024, 260)
        self._kb_frame.setVisible(False)

        kb_layout = QVBoxLayout(self._kb_frame)
        kb_layout.setContentsMargins(0, 0, 0, 0)
        kb_layout.setSpacing(0)

        from app.gui.widgets.on_screen_keyboard import OnScreenKeyboard
        self._kb = OnScreenKeyboard(parent=self._kb_frame)
        kb_layout.addWidget(self._kb)

        self._kb.text_changed.connect(self._kb_text_changed)
        self._kb.enter_pressed.connect(self._kb_done)
        self._kb.cancelled.connect(self._kb_done)

    # ── Helpers ────────────────────────────────────────────────────────

    def _lbl(self, text):
        l = QLabel(text)
        l.setFont(QFont("Arial", 18, QFont.Bold))
        return l

    def _field(self, placeholder):
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setMinimumHeight(50)
        w.setReadOnly(True)
        w.setFont(QFont("Arial", 18))
        w.setStyleSheet("""
            QLineEdit{font-size:18px;padding:8px;
                border:2px solid #bdc3c7;border-radius:5px;background:white;}
            QLineEdit:focus{border-color:#3498db;}
        """)
        return w

    def _activate(self, field):

        """Show keyboard — no layout shift since it is absolutely positioned."""
        self._active_input = field
        self._kb.set_text(field.text())
        self._kb_frame.setVisible(True)
        self._kb_frame.raise_()

    def _kb_text_changed(self, text):
        if self._active_input:
            self._active_input.setText(text)

    def _kb_done(self):
        self._kb_frame.setVisible(False)
        self._active_input = None

    # ════════════════════════════════════════════════════════════════════
    # SECTION: SAVE
    # ════════════════════════════════════════════════════════════════════

    def accept(self):
        if self.recording:
            try:
                metadata = self.get_metadata()
                meta_controller = MetadataController()
                success, updated_recording, error = meta_controller.add_metadata(
                    self.recording, metadata)
                if not success:
                    QMessageBox.warning(self, "Save Error",
                        f"Recording saved successfully!\n\n"
                        f"However, the recording information could not be saved:\n"
                        f"{error}\n\nYou can add this information later.")
                    logger.error(f"Recording info save failed: {error}")
                    super().accept(); return
                logger.info(f"Recording info saved for: {self.recording.filename}")
                super().accept()
            except Exception as e:
                QMessageBox.critical(self, "Unexpected Error",
                    f"An unexpected error occurred:\n\n{str(e)}\n\n"
                    f"Your recording is safe, but information was not saved.")
                logger.error(f"Exception: {e}", exc_info=True)
                super().accept()
        else:
            super().accept()

    # ════════════════════════════════════════════════════════════════════
    # SECTION: GET METADATA
    # ════════════════════════════════════════════════════════════════════

    def get_metadata(self) -> RecordingMetadata:
        metadata = RecordingMetadata()
        metadata.patient_name      = self.patient_input.text().strip()
        metadata.procedure         = self.procedure_combo.currentText()
        metadata.operating_theatre = self.ot_combo.currentText()
        metadata.surgeon_name      = self.consultant_input.text().strip()
        logger.debug(f"Collected recording info: patient={metadata.patient_name}")
        return metadata


__all__ = ['MetadataDialog']
