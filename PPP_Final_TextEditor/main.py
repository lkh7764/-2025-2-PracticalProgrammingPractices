# main.py
from __future__ import annotations
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QInputDialog, QMessageBox,
    QToolBar, QLabel
)
from PyQt6.QtGui import QAction, QKeySequence

from editor_widget import EditorWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("[2025-2 PPP] Text Editor (Custom Buffer)")

        self.editor = EditorWidget(self)
        self.setCentralWidget(self.editor)

        self.current_path: str | None = None

        self._make_actions()
        self._make_menu()
        self._make_toolbar()
        self._make_statusbar()

        self.resize(900, 650)

    def _make_actions(self):
        self.act_open = QAction("Open...", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self.on_open)

        self.act_save = QAction("Save", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.triggered.connect(self.on_save)

        self.act_save_as = QAction("Save As...", self)
        self.act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.act_save_as.triggered.connect(self.on_save_as)

        self.act_undo = QAction("Undo", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.triggered.connect(self.editor.do_undo)

        self.act_redo = QAction("Redo", self)
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.act_redo.triggered.connect(self.editor.do_redo)

        self.act_find = QAction("Find (Next)...", self)
        self.act_find.setShortcut(QKeySequence("Ctrl+F"))
        self.act_find.triggered.connect(self.on_find_next)

        self.act_replace = QAction("Replace (Next)...", self)
        self.act_replace.setShortcut(QKeySequence("Ctrl+H"))
        self.act_replace.triggered.connect(self.on_replace_next)

        self.act_replace_all = QAction("Replace All...", self)
        self.act_replace_all.triggered.connect(self.on_replace_all)

    def _make_menu(self):
        m_file = self.menuBar().addMenu("File")
        m_file.addAction(self.act_open)
        m_file.addAction(self.act_save)
        m_file.addAction(self.act_save_as)

        m_edit = self.menuBar().addMenu("Edit")
        m_edit.addAction(self.act_undo)
        m_edit.addAction(self.act_redo)
        m_edit.addSeparator()
        m_edit.addAction(self.act_find)
        m_edit.addAction(self.act_replace)
        m_edit.addAction(self.act_replace_all)

    def _make_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        tb.addAction(self.act_open)
        tb.addAction(self.act_save)
        tb.addSeparator()
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)
        tb.addSeparator()
        tb.addAction(self.act_find)
        tb.addAction(self.act_replace)

    def _make_statusbar(self):
        self.status = QLabel("Ready")
        self.statusBar().addWidget(self.status)

    def on_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        try:
            self.editor.open_file(path)
            self.current_path = path
            self.status.setText(f"Opened: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Open failed", str(e))

    def on_save(self):
        if not self.current_path:
            self.on_save_as()
            return
        try:
            self.editor.save_file(self.current_path)
            self.status.setText(f"Saved: {self.current_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def on_save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return
        try:
            self.editor.save_file(path)
            self.current_path = path
            self.status.setText(f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _ask_find_replace(self, ask_replace: bool):
        query, ok = QInputDialog.getText(self, "Find", "Find what?")
        if not ok:
            return None
        query = query or ""
        repl = ""
        if ask_replace:
            repl, ok2 = QInputDialog.getText(self, "Replace", "Replace with?")
            if not ok2:
                return None
        self.editor.set_find_replace(query, repl)
        return query, repl

    def on_find_next(self):
        res = self._ask_find_replace(ask_replace=False)
        if res is None:
            return
        self.editor.find_next()
        self.status.setText(f"Find next: {self.editor.find_query}")

    def on_replace_next(self):
        res = self._ask_find_replace(ask_replace=True)
        if res is None:
            return
        self.editor.replace_next()
        self.status.setText(f"Replace next: {self.editor.find_query} -> {self.editor.replace_text}")

    def on_replace_all(self):
        res = self._ask_find_replace(ask_replace=True)
        if res is None:
            return
        self.editor.replace_all()
        self.status.setText(f"Replace all: {self.editor.find_query} -> {self.editor.replace_text}")


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
