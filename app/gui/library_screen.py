"""
File: app/gui/library_screen.py

Library Screen — QTableWidget with checkbox multi-select.

LAYOUT:
  Title row  ("Video Library" left | stretch | count + selection right)
  Search bar (field + keyboard btn + search btn)
  QTableWidget (checkbox | patient | procedure | date | duration)
  Single button row (Select All | Clear | Refresh | Edit | Export | Delete)

SELECTION UX:
  Tap checkbox     -> toggle row selection
  Double-tap row   -> play video (only if exactly 1 selected)
  Select All btn   -> check all checkboxes
  Clear btn        -> uncheck all

BUTTON STATES:
  0 selected  -> Edit/Export/Delete disabled
  1 selected  -> Edit/Export/Delete enabled
  2+ selected -> Edit disabled, Export/Delete enabled

KEYBOARD:
  Appears at bottom of widget when search field tapped
  Y position computed dynamically: self.height() - ONSCREEN_KB_HEIGHT
  Hides when Search button clicked or 5s idle
  Solid background (setAutoFillBackground on keyboard widget) covers
  table/buttons behind it — no see-through gaps

NAVIGATION:
  Nav bar (REC/LIB/SET) is always visible — no back button needed here

CHECKBOX:
  Indicator size: LIB_CHECKBOX_SIZE (36px) — touch-friendly within 52px row

All sizes/fonts from app_config.py LIB_* constants.

Author: OT Video Dev Team / ZKB
Date: April 9, 2026
Version: 3.3.0
Changelog:
  v3.3.0: Removed < REC back button — nav bar always visible, redundant.
          Title row simplified: left-aligned title, count/selection right.
  v3.2.0: Added < REC back button. Title centred. Checkbox 36px indicator.
  v3.1.0: Config-driven KB height. Dynamic Y position.
  v3.0.0: QTableWidget, checkbox multi-select.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLineEdit, QLabel, QMessageBox,
    QFrame, QProgressDialog, QFileDialog,
    QDialog, QDialogButtonBox, QCheckBox, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import shutil
from pathlib import Path

from app.controllers.library_controller import LibraryController
from app.gui.widgets.on_screen_keyboard import OnScreenKeyboard
from app.utils.logger import AppLogger

logger = AppLogger("LibraryScreen")

# ── Import config constants ────────────────────────────────────────────────────
try:
    from config.app_config import (
        LIB_SEARCH_FONT, LIB_SEARCH_HEIGHT,
        LIB_SEARCH_BTN_W, LIB_SEARCH_BTN_H, LIB_SEARCH_BTN_FONT,
        LIB_KB_BTN_SIZE, LIB_LABEL_FONT,
        LIB_TABLE_FONT, LIB_TABLE_ROW_H, LIB_TABLE_HDR_FONT,
        LIB_SCROLLBAR_W, LIB_BTN_H, LIB_BTN_FONT,
        LIB_TITLE_FONT, LIB_COUNT_FONT, LIB_COUNT_COLOR,
        LIB_SELECT_FONT, LIB_SELECT_COLOR,
        ONSCREEN_KB_HEIGHT,
    )
    try:
        from config.app_config import LIB_CHECKBOX_SIZE
    except ImportError:
        LIB_CHECKBOX_SIZE = 36

except ImportError:
    LIB_SEARCH_FONT=18;  LIB_SEARCH_HEIGHT=55
    LIB_SEARCH_BTN_W=160; LIB_SEARCH_BTN_H=55; LIB_SEARCH_BTN_FONT=16
    LIB_KB_BTN_SIZE=75;  LIB_LABEL_FONT=16
    LIB_TABLE_FONT=15;   LIB_TABLE_ROW_H=52; LIB_TABLE_HDR_FONT=15
    LIB_SCROLLBAR_W=32;  LIB_BTN_H=55; LIB_BTN_FONT=14
    LIB_TITLE_FONT=20;   LIB_COUNT_FONT=14; LIB_COUNT_COLOR="#555"
    LIB_SELECT_FONT=14;  LIB_SELECT_COLOR="#1a3fa0"
    ONSCREEN_KB_HEIGHT=253; LIB_CHECKBOX_SIZE=36

# ── Table column indices ───────────────────────────────────────────────────────
COL_CHECK    = 0
COL_PATIENT  = 1
COL_PROC     = 2
COL_DATE     = 3
COL_DURATION = 4

# ── Keyboard width ─────────────────────────────────────────────────────────────
KB_WIDTH = 1024

# ── Checkbox indicator QSS ─────────────────────────────────────────────────────
def _checkbox_style():
    sz = LIB_CHECKBOX_SIZE
    return f"""
        QCheckBox {{ margin-left: 8px; }}
        QCheckBox::indicator {{
            width:  {sz}px;
            height: {sz}px;
            border: 2px solid #95a5a6;
            border-radius: 4px;
            background: white;
        }}
        QCheckBox::indicator:unchecked:hover {{
            border-color: #3498db;
        }}
        QCheckBox::indicator:checked {{
            background-color: #27ae60;
            border-color:     #1e8449;
        }}
    """


def _btn_style(bg, hover, pressed, font=None, disabled_bg='#bdc3c7'):
    """Generate 3D button stylesheet."""
    f = font or LIB_BTN_FONT
    return f"""
        QPushButton {{
            background-color: {bg};
            color: white;
            border-top:    2px solid rgba(255,255,255,0.35);
            border-left:   2px solid rgba(255,255,255,0.35);
            border-bottom: 2px solid rgba(0,0,0,0.35);
            border-right:  2px solid rgba(0,0,0,0.35);
            border-radius: 6px;
            font-size: {f}px;
            font-weight: bold;
        }}
        QPushButton:pressed {{
            background-color: {pressed};
            border-top:    2px solid rgba(0,0,0,0.35);
            border-left:   2px solid rgba(0,0,0,0.35);
            border-bottom: 2px solid rgba(255,255,255,0.35);
            border-right:  2px solid rgba(255,255,255,0.35);
        }}
        QPushButton:disabled {{
            background-color: {disabled_bg};
            color: #7f8c8d;
            border: 2px solid #bdc3c7;
        }}
    """


class LibraryScreen(QWidget):
    """Library screen with QTableWidget and checkbox multi-select."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller         = LibraryController()
        self.keyboard           = None
        self._kb_idle_timer     = None
        self.current_recordings = []
        self.main_window        = parent
        self.init_ui()
        self.refresh()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: UI BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 0, 10, 2)

        # ── Title row ─────────────────────────────────────────────────────────
        # Nav bar (REC/LIB/SET) is always visible — no back button needed here
        title_row = QHBoxLayout()

        title = QLabel("Video Library")
        title.setFont(QFont("Arial", LIB_TITLE_FONT, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        title_row.addWidget(title)

        title_row.addStretch()

        self.count_label = QLabel("Loading...")
        self.count_label.setFont(QFont("Arial", LIB_COUNT_FONT))
        self.count_label.setStyleSheet(f"color: {LIB_COUNT_COLOR};")
        title_row.addWidget(self.count_label)
        title_row.addSpacing(20)

        self.selection_label = QLabel("")
        self.selection_label.setFont(QFont("Arial", LIB_SELECT_FONT, QFont.Bold))
        self.selection_label.setStyleSheet(f"color: {LIB_SELECT_COLOR};")
        title_row.addWidget(self.selection_label)

        layout.addLayout(title_row)

        # ── Search bar ────────────────────────────────────────────────────────
        search_frame = QFrame()
        search_frame.setStyleSheet(
            "QFrame{background:#ecf0f1;border-radius:6px;padding:4px;}")
        sf = QHBoxLayout(search_frame)
        sf.setSpacing(8)

        search_lbl = QLabel("Search:")
        search_lbl.setFont(QFont("Arial", LIB_LABEL_FONT, QFont.Bold))
        sf.addWidget(search_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by patient name...")
        self.search_input.setMinimumHeight(LIB_SEARCH_HEIGHT)
        self.search_input.setFont(QFont("Arial", LIB_SEARCH_FONT))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: {LIB_SEARCH_FONT}px; padding: 8px;
                border: 2px solid #bdc3c7; border-radius: 5px;
                background: white;
            }}
            QLineEdit:focus {{ border-color: #3498db; }}
        """)
        self.search_input.returnPressed.connect(self._do_search)
        self.search_input.mousePressEvent = lambda e: self._show_keyboard(e)
        sf.addWidget(self.search_input, 2)

        kb_btn = QPushButton("KB")
        kb_btn.setFixedSize(LIB_KB_BTN_SIZE, LIB_SEARCH_HEIGHT)
        kb_btn.setFont(QFont("Arial", 18, QFont.Bold))
        kb_btn.setStyleSheet(
            "QPushButton{background:#3498db;color:white;border-radius:5px;"
            "font-weight:bold;}"
            "QPushButton:pressed{background:#2980b9;}")
        kb_btn.clicked.connect(lambda: self._show_keyboard(None))
        sf.addWidget(kb_btn)

        search_btn = QPushButton("Search")
        search_btn.setMinimumSize(LIB_SEARCH_BTN_W, LIB_SEARCH_BTN_H)
        search_btn.setFont(QFont("Arial", LIB_SEARCH_BTN_FONT, QFont.Bold))
        search_btn.setStyleSheet(_btn_style(
            '#27ae60', '#229954', '#1a7a40', font=LIB_SEARCH_BTN_FONT))
        search_btn.clicked.connect(self._on_search_btn)
        sf.addWidget(search_btn)

        layout.addWidget(search_frame)

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "", "Patient Name", "Procedure", "Date / Time", "Duration"
        ])

        self.table.setColumnWidth(COL_CHECK,    65)
        self.table.setColumnWidth(COL_PATIENT,  240)
        self.table.setColumnWidth(COL_PROC,     220)
        self.table.setColumnWidth(COL_DATE,     210)
        self.table.setColumnWidth(COL_DURATION, 130)

        self.table.horizontalHeader().setSectionResizeMode(
            COL_PATIENT, QHeaderView.Stretch)
        self.table.horizontalHeader().setFont(
            QFont("Arial", LIB_TABLE_HDR_FONT, QFont.Bold))
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: {LIB_TABLE_FONT}px;
                background: white;
                alternate-background-color: #f5f7fa;
                gridline-color: #dde1e5;
            }}
            QTableWidget::item {{ padding: 6px; }}
            QTableWidget::item:selected {{
                background-color: #d6eaf8;
                color: #1a1a1a;
            }}
            QHeaderView::section {{
                background-color: #2c3e50;
                color: white;
                padding: 8px;
                font-size: {LIB_TABLE_HDR_FONT}px;
                font-weight: bold;
                border: none;
            }}
            QScrollBar:vertical {{
                width: {LIB_SCROLLBAR_W}px;
                background: #ecf0f1;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #95a5a6;
                border-radius: 4px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{ background: #7f8c8d; }}
        """)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        # ── Single button row ─────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        sel_all = QPushButton("Select All")
        sel_all.setMinimumHeight(LIB_BTN_H)
        sel_all.setStyleSheet(_btn_style('#9b59b6', '#8e44ad', '#6c3483'))
        sel_all.clicked.connect(self.select_all)
        btn_row.addWidget(sel_all)

        clr_sel = QPushButton("Clear")
        clr_sel.setMinimumHeight(LIB_BTN_H)
        clr_sel.setStyleSheet(_btn_style('#95a5a6', '#7f8c8d', '#626567'))
        clr_sel.clicked.connect(self.clear_selection)
        btn_row.addWidget(clr_sel)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setMinimumHeight(LIB_BTN_H)
        refresh_btn.setStyleSheet(_btn_style('#3498db', '#2980b9', '#1f618d'))
        refresh_btn.clicked.connect(self.refresh)
        btn_row.addWidget(refresh_btn)

        self.edit_btn = QPushButton("Edit Name")
        self.edit_btn.setMinimumHeight(LIB_BTN_H)
        self.edit_btn.setStyleSheet(_btn_style('#16a085', '#138d75', '#0e6655'))
        self.edit_btn.clicked.connect(self.edit_filename)
        self.edit_btn.setEnabled(False)
        btn_row.addWidget(self.edit_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.setMinimumHeight(LIB_BTN_H)
        self.export_btn.setStyleSheet(_btn_style('#f39c12', '#d68910', '#9a6109'))
        self.export_btn.clicked.connect(self.export_selected)
        self.export_btn.setEnabled(False)
        btn_row.addWidget(self.export_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setMinimumHeight(LIB_BTN_H)
        self.delete_btn.setStyleSheet(_btn_style('#e74c3c', '#cb4335', '#922b21'))
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        btn_row.addWidget(self.delete_btn)

        layout.addLayout(btn_row)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: DATA DISPLAY
    # ─────────────────────────────────────────────────────────────────────────

    def refresh(self):
        """Load all recordings and display."""
        self.search_input.clear()
        success, recs, error = self.controller.get_all_recordings(limit=200)
        if not success:
            QMessageBox.warning(self, "Error", f"Failed to load: {error}")
            return
        self.current_recordings = recs
        self._display(recs)

    def _display(self, recs):
        """Populate table with recordings."""
        self.table.setRowCount(0)

        if not recs:
            self.count_label.setText("No recordings found")
            self.selection_label.setText("")
            self._update_buttons()
            return

        self.count_label.setText(f"{len(recs)} recording(s)")
        self.table.setRowCount(len(recs))

        for row, r in enumerate(recs):
            self.table.setRowHeight(row, LIB_TABLE_ROW_H)

            # Checkbox — enlarged indicator for reliable touch target
            chk = QCheckBox()
            chk.setStyleSheet(_checkbox_style())
            chk.stateChanged.connect(self._on_checkbox_changed)
            self.table.setCellWidget(row, COL_CHECK, chk)

            pat = QTableWidgetItem(r.patient_name or "—")
            pat.setFont(QFont("Arial", LIB_TABLE_FONT))
            pat.setData(Qt.UserRole, r.id)
            self.table.setItem(row, COL_PATIENT, pat)

            proc = QTableWidgetItem(r.procedure_name or "—")
            proc.setFont(QFont("Arial", LIB_TABLE_FONT))
            self.table.setItem(row, COL_PROC, proc)

            dt = f"{r.recording_date or ''} {r.recording_time or ''}".strip()
            date_item = QTableWidgetItem(dt or "—")
            date_item.setFont(QFont("Arial", LIB_TABLE_FONT))
            self.table.setItem(row, COL_DATE, date_item)

            if r.duration_seconds:
                m   = r.duration_seconds // 60
                s   = r.duration_seconds % 60
                dur = f"{m}m {s:02d}s"
            else:
                dur = "—"
            dur_item = QTableWidgetItem(dur)
            dur_item.setFont(QFont("Arial", LIB_TABLE_FONT))
            dur_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, COL_DURATION, dur_item)

        self._update_buttons()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: SELECTION LOGIC
    # ─────────────────────────────────────────────────────────────────────────

    def _checked_rows(self):
        rows = []
        for r in range(self.table.rowCount()):
            w = self.table.cellWidget(r, COL_CHECK)
            if w and w.isChecked():
                rows.append(r)
        return rows

    def _checked_recordings(self):
        recs = []
        for row in self._checked_rows():
            item = self.table.item(row, COL_PATIENT)
            if item:
                rec_id = item.data(Qt.UserRole)
                rec = next((r for r in self.current_recordings
                            if r.id == rec_id), None)
                if rec:
                    recs.append(rec)
        return recs

    def _on_checkbox_changed(self):
        self._update_buttons()

    def _update_buttons(self):
        count = len(self._checked_rows())
        if count == 0:
            self.selection_label.setText("")
            self.edit_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        elif count == 1:
            self.selection_label.setText("1 file selected")
            self.edit_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.selection_label.setText(f"{count} files selected")
            self.edit_btn.setEnabled(False)
            self.export_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

    def select_all(self):
        for r in range(self.table.rowCount()):
            w = self.table.cellWidget(r, COL_CHECK)
            if w:
                w.setChecked(True)

    def clear_selection(self):
        for r in range(self.table.rowCount()):
            w = self.table.cellWidget(r, COL_CHECK)
            if w:
                w.setChecked(False)

    def _on_double_click(self, index):
        """Play video on double-tap — only if exactly 1 checked."""
        if len(self._checked_rows()) != 1:
            return
        row    = index.row()
        item   = self.table.item(row, COL_PATIENT)
        if not item:
            return
        rec_id = item.data(Qt.UserRole)
        rec    = next((r for r in self.current_recordings
                       if r.id == rec_id), None)
        if not rec:
            return
        if self.main_window and hasattr(self.main_window, 'playback_screen'):
            self.main_window.playback_screen.load_video(rec)
            self.main_window.screens.setCurrentWidget(
                self.main_window.playback_screen)
            logger.info(f"Playing: {rec.filename}")
        else:
            QMessageBox.warning(self, "Error", "Playback unavailable")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: SEARCH
    # ─────────────────────────────────────────────────────────────────────────

    def _on_search_btn(self):
        self._hide_keyboard()
        self._do_search()

    def _do_search(self):
        text = self.search_input.text().strip()
        if not text:
            self.refresh()
            return
        success, recs, error = self.controller.search_recordings(
            patient_name=text)
        if not success:
            QMessageBox.warning(self, "Error", f"Search failed: {error}")
            return
        self.current_recordings = recs
        self._display(recs)
        if not recs:
            QMessageBox.information(self, "No Results",
                f"No recordings found for: {text}")

    def search(self):
        """Public search method — kept for compatibility."""
        self._do_search()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: KEYBOARD
    # ─────────────────────────────────────────────────────────────────────────

    def _show_keyboard(self, event):
        """Show keyboard anchored to bottom of this widget."""
        if event:
            QLineEdit.mousePressEvent(self.search_input, event)

        if not self.keyboard:
            self.keyboard = OnScreenKeyboard(self)
            kb_y = self.height() - ONSCREEN_KB_HEIGHT
            self.keyboard.setGeometry(0, kb_y, KB_WIDTH, ONSCREEN_KB_HEIGHT)

            self.keyboard.text_changed.connect(self.search_input.setText)
            self.keyboard.enter_pressed.connect(self._on_search_btn)
            self.keyboard.cancelled.connect(self._hide_keyboard)

            self._kb_idle_timer = QTimer(self)
            self._kb_idle_timer.setSingleShot(True)
            self._kb_idle_timer.setInterval(5000)
            self._kb_idle_timer.timeout.connect(self._hide_keyboard)
            self.keyboard.text_changed.connect(
                lambda _: self._kb_idle_timer.start())

        self.keyboard.set_text(self.search_input.text())
        self.keyboard.setVisible(True)
        self.keyboard.raise_()
        self._kb_idle_timer.start()

    def _hide_keyboard(self):
        if self.keyboard:
            self.keyboard.setVisible(False)
        if self._kb_idle_timer:
            self._kb_idle_timer.stop()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION: ACTIONS
    # ─────────────────────────────────────────────────────────────────────────

    def delete_selected(self):
        recs = self._checked_recordings()
        if not recs:
            return
        count = len(recs)
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {count} recording(s)?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        deleted = 0
        for rec in recs:
            ok, _, err = self.controller.delete_recording(rec.id, True)
            if ok:
                deleted += 1
        QMessageBox.information(self, "Done",
            f"Deleted {deleted} of {count} recording(s).")
        self.refresh()

    def export_selected(self):
        recs = self._checked_recordings()
        if not recs:
            return
        count = len(recs)
        dest  = QFileDialog.getExistingDirectory(
            self, f"Export {count} file(s) to...")
        if not dest:
            return
        prog = QProgressDialog(
            f"Exporting {count} file(s)...", "Cancel", 0, count, self)
        prog.setWindowModality(Qt.WindowModal)
        prog.setMinimumDuration(0)
        exported = 0
        for idx, rec in enumerate(recs):
            if prog.wasCanceled():
                break
            if Path(rec.filepath).exists():
                try:
                    shutil.copy2(rec.filepath, Path(dest) / rec.filename)
                    exported += 1
                except Exception:
                    pass
            prog.setValue(idx + 1)
        QMessageBox.information(self, "Done",
            f"Exported {exported} of {count} recording(s).")

    def edit_filename(self):
        recs = self._checked_recordings()
        if len(recs) != 1:
            return
        rec = recs[0]

        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Filename")
        dlg.setMinimumWidth(500)
        dlg.setModal(True)
        layout = QVBoxLayout(dlg)

        lbl = QLabel("New name (without .mp4):")
        lbl.setFont(QFont("Arial", 14))
        layout.addWidget(lbl)

        name_input = QLineEdit(Path(rec.filename).stem)
        name_input.setMinimumHeight(50)
        name_input.setFont(QFont("Arial", 14))
        layout.addWidget(name_input)

        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec_() == QDialog.Accepted:
            new_name = name_input.text().strip()
            if new_name and new_name != Path(rec.filename).stem:
                try:
                    old_path = Path(rec.filepath)
                    new_path = old_path.parent / f"{new_name}.mp4"
                    old_path.rename(new_path)
                    from app.services.database_service import DatabaseService
                    DatabaseService().update_recording(
                        rec.id,
                        filename=f"{new_name}.mp4",
                        filepath=str(new_path))
                    QMessageBox.information(self, "Done", "File renamed.")
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))


__all__ = ['LibraryScreen']
