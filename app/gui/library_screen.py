"""
File: app/gui/library_screen.py

Library screen with proper multi-select logic:
- 1 file selected: Edit/Export/Delete active, double-click plays
- Multiple selected: Only Export/Delete active, double-click disabled

Version: 2.3.0 (Fixed double-click logic)
Date: February 9, 2026
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QLabel, QMessageBox, QFrame,
    QProgressDialog, QFileDialog, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import shutil
from pathlib import Path

from app.controllers.library_controller import LibraryController
from app.gui.widgets.on_screen_keyboard import OnScreenKeyboard
from app.utils.logger import AppLogger

logger = AppLogger("LibraryScreen")


class LibraryScreen(QWidget):
    """Library with smart selection logic."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = LibraryController()
        self.keyboard = None
        self.current_recordings = []
        self.main_window = parent
        
        self.init_ui()
        self.refresh()
    
    def init_ui(self):
        """Build UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Video Library")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Search
        search_frame = QFrame()
        search_frame.setStyleSheet("QFrame { background-color: #ecf0f1; border-radius: 5px; padding: 10px; }")
        search_layout = QHBoxLayout(search_frame)
        
        search_label = QLabel("Search:")
        search_label.setFont(QFont("Arial", 14, QFont.Bold))
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by patient...")
        self.search_input.setMinimumHeight(50)
        self.search_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus { border-color: #3498db; }
        """)
        self.search_input.returnPressed.connect(self.search)
        self.search_input.mousePressEvent = lambda e: self._show_search_keyboard(e)
        search_layout.addWidget(self.search_input, 3)
        
        kb_btn = QPushButton("⌨")
        kb_btn.setFixedSize(60, 50)
        kb_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; border-radius: 5px; font-size: 24px; }")
        kb_btn.clicked.connect(lambda: self._show_search_keyboard(None))
        search_layout.addWidget(kb_btn)
        
        search_btn = QPushButton("Search")
        search_btn.setMinimumSize(120, 50)
        search_btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; border-radius: 5px; font-size: 16px; font-weight: bold; }")
        search_btn.clicked.connect(self.search)
        search_layout.addWidget(search_btn)
        
        layout.addWidget(search_frame)
        
        # Info
        info_layout = QHBoxLayout()
        self.count_label = QLabel("Loading...")
        self.count_label.setStyleSheet("color: gray; font-size: 14px;")
        info_layout.addWidget(self.count_label)
        info_layout.addStretch()
        
        self.selection_label = QLabel("")
        self.selection_label.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold;")
        info_layout.addWidget(self.selection_label)
        layout.addLayout(info_layout)
        
        # List
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover { background-color: #d5dbdb; }
            QListWidget::item:selected {
                background-color: #3498db !important;
                color: white !important;
            }
            QListWidget::item:selected:hover {
                background-color: #2980b9 !important;
            }
        """)
        self.list_widget.itemSelectionChanged.connect(self.update_selection_info)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        # Buttons row 1
        row1 = QHBoxLayout()
        row1.setSpacing(15)
        
        sel_all = QPushButton("Select All")
        sel_all.setMinimumSize(120, 60)
        sel_all.setStyleSheet("QPushButton { background-color: #9b59b6; color: white; border-radius: 5px; font-size: 14px; font-weight: bold; }")
        sel_all.clicked.connect(self.select_all)
        row1.addWidget(sel_all)
        
        clr_sel = QPushButton("Clear Selection")
        clr_sel.setMinimumSize(120, 60)
        clr_sel.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border-radius: 5px; font-size: 14px; font-weight: bold; }")
        clr_sel.clicked.connect(self.clear_selection)
        row1.addWidget(clr_sel)
        
        refresh = QPushButton("Refresh")
        refresh.setMinimumSize(120, 60)
        refresh.setStyleSheet("QPushButton { background-color: #3498db; color: white; border-radius: 5px; font-size: 16px; font-weight: bold; }")
        refresh.clicked.connect(self.refresh)
        row1.addWidget(refresh)
        
        row1.addStretch()
        layout.addLayout(row1)
        
        # Buttons row 2
        row2 = QHBoxLayout()
        row2.setSpacing(15)
        row2.addStretch()
        
        self.edit_btn = QPushButton("Edit Name")
        self.edit_btn.setMinimumSize(150, 60)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_filename)
        self.edit_btn.setEnabled(False)
        row2.addWidget(self.edit_btn)
        
        self.export_btn = QPushButton("Export Selected")
        self.export_btn.setMinimumSize(180, 60)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.export_btn.clicked.connect(self.export_selected)
        self.export_btn.setEnabled(False)
        row2.addWidget(self.export_btn)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setMinimumSize(180, 60)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        row2.addWidget(self.delete_btn)
        
        layout.addLayout(row2)
    
    def _show_search_keyboard(self, event):
        if event:
            QLineEdit.mousePressEvent(self.search_input, event)
        if not self.keyboard:
            self.keyboard = OnScreenKeyboard(self)
            self.keyboard.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.keyboard.set_text(self.search_input.text())
        try: self.keyboard.text_changed.disconnect()
        except: pass
        self.keyboard.text_changed.connect(self.search_input.setText)
        try: self.keyboard.enter_pressed.disconnect()
        except: pass
        self.keyboard.enter_pressed.connect(lambda: (self.keyboard.hide(), self.search()))
        try: self.keyboard.cancelled.disconnect()
        except: pass
        self.keyboard.cancelled.connect(self.keyboard.hide)
        self.keyboard.show_keyboard()
    
    def search(self):
        text = self.search_input.text().strip()
        if not text:
            self.refresh()
            return
        success, recs, error = self.controller.search_recordings(patient_name=text)
        if not success:
            QMessageBox.warning(self, "Error", f"Search failed: {error}")
            return
        self.current_recordings = recs
        self._display_recordings(recs)
    
    def refresh(self):
        self.list_widget.clear()
        self.search_input.clear()
        success, recs, error = self.controller.get_all_recordings(limit=100)
        if not success:
            QMessageBox.warning(self, "Error", f"Failed: {error}")
            return
        self.current_recordings = recs
        self._display_recordings(recs)
    
    def _display_recordings(self, recs):
        self.list_widget.clear()
        if not recs:
            self.count_label.setText("No recordings")
            item = QListWidgetItem("No recordings")
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            return
        
        self.count_label.setText(f"Found {len(recs)} recording(s)")
        for r in recs:
            pat = r.patient_name or "No patient"
            proc = r.procedure_name or "No procedure"
            dur_m = r.duration_seconds // 60
            dur_s = r.duration_seconds % 60
            size = r.file_size_bytes / (1024**2) if r.file_size_bytes else 0
            txt = f"Patient: {pat}\nProcedure: {proc}\nDate: {r.recording_date} {r.recording_time}\n" + \
                  f"Duration: {dur_m}m {dur_s}s | Size: {size:.1f} MB\nOT: {r.operating_theatre or 'Not specified'}"
            item = QListWidgetItem(txt.strip())
            item.setData(Qt.UserRole, r.id)
            self.list_widget.addItem(item)
    
    def update_selection_info(self):
        """
        Update button states based on selection count.
        
        LOGIC:
        - 0 selected: All disabled
        - 1 selected: Edit/Export/Delete enabled, playback allowed
        - 2+ selected: Only Export/Delete enabled, playback BLOCKED
        """
        count = len(self.list_widget.selectedItems())
        
        if count == 0:
            self.selection_label.setText("")
            self.edit_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        elif count == 1:
            self.selection_label.setText("1 file (double-click to play)")
            self.edit_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.selection_label.setText(f"{count} files (double-click disabled)")
            self.edit_btn.setEnabled(False)
            self.export_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
    
    def select_all(self):
        self.list_widget.selectAll()
    
    def clear_selection(self):
        self.list_widget.clearSelection()
    
    def on_item_double_clicked(self, item):
        """
        Double-click handler with multi-select protection.
        
        ONLY plays video if exactly 1 file selected.
        Prevents conflict with multi-select operations.
        """
        selected_count = len(self.list_widget.selectedItems())
        
        if selected_count != 1:
            # Multiple selected - do nothing
            logger.debug(f"Double-click ignored - {selected_count} files selected")
            return
        
        rec_id = item.data(Qt.UserRole)
        rec = None
        for r in self.current_recordings:
            if r.id == rec_id:
                rec = r
                break
        
        if not rec:
            QMessageBox.warning(self, "Error", "Recording not found")
            return
        
        if self.main_window and hasattr(self.main_window, 'playback_screen'):
            self.main_window.playback_screen.load_video(rec)
            self.main_window.screens.setCurrentWidget(self.main_window.playback_screen)
            logger.info(f"Playing: {rec.filename}")
        else:
            QMessageBox.warning(self, "Error", "Playback unavailable")
    
    def delete_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
        count = len(items)
        reply = QMessageBox.question(self, "Confirm", f"Delete {count} recording(s)?", 
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        
        deleted = 0
        for item in items:
            success, _, error = self.controller.delete_recording(item.data(Qt.UserRole), True)
            if success:
                deleted += 1
        
        QMessageBox.information(self, "Done", f"Deleted {deleted} of {count}")
        self.refresh()
    
    def export_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
        count = len(items)
        dest = QFileDialog.getExistingDirectory(self, f"Export {count} file(s)")
        if not dest:
            return
        
        prog = QProgressDialog(f"Exporting {count}...", "Cancel", 0, count, self)
        prog.setWindowModality(Qt.WindowModal)
        prog.setMinimumDuration(0)
        
        exported = 0
        for idx, item in enumerate(items):
            if prog.wasCanceled():
                break
            rec = next((r for r in self.current_recordings if r.id == item.data(Qt.UserRole)), None)
            if rec and Path(rec.filepath).exists():
                try:
                    shutil.copy2(rec.filepath, Path(dest) / rec.filename)
                    exported += 1
                except: pass
            prog.setValue(idx + 1)
        
        QMessageBox.information(self, "Done", f"Exported {exported} of {count}")
    
    def edit_filename(self):
        items = self.list_widget.selectedItems()
        if len(items) != 1:
            return
        rec = next((r for r in self.current_recordings if r.id == items[0].data(Qt.UserRole)), None)
        if not rec:
            return
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Filename")
        dlg.setMinimumWidth(500)
        layout = QVBoxLayout(dlg)
        
        layout.addWidget(QLabel("New name (without .mp4):"))
        name_input = QLineEdit(Path(rec.filename).stem)
        name_input.setMinimumHeight(50)
        layout.addWidget(name_input)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        
        if dlg.exec_() == QDialog.Accepted:
            new_name = name_input.text().strip()
            if new_name and new_name != Path(rec.filename).stem:
                try:
                    old = Path(rec.filepath)
                    new = old.parent / f"{new_name}.mp4"
                    old.rename(new)
                    from app.services.database_service import DatabaseService
                    DatabaseService().update_recording(rec.id, filename=f"{new_name}.mp4", filepath=str(new))
                    QMessageBox.information(self, "Done", "Renamed")
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))


__all__ = ['LibraryScreen']
