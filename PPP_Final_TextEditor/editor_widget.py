# editor_widget.py
from __future__ import annotations
from typing import Optional
from PyQt6.QtCore import Qt, QRect, QTimer
from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QKeyEvent
from PyQt6.QtWidgets import QWidget

from core import TextBuffer, Cursor, UndoStack, InsertCommand, DeleteCommand


class EditorWidget(QWidget):
    """
    QPlainTextEdit 없이:
    - paintEvent에서 직접 텍스트/커서 렌더
    - keyPressEvent로 입력 처리
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.buf = TextBuffer("")
        self.cursor = Cursor(0, 0)
        self.undo = UndoStack()

        self.font = QFont("Consolas")
        if self.font==None: self.font = QFont("Menlo")

        self.font.setPointSize(12)
        self.setFont(self.font)
        self.fm = QFontMetrics(self.font)

        self.padding = 8
        self.line_h = self.fm.height()
        self.char_w = self.fm.horizontalAdvance("M")

        # cursor blink (optional, cheap)
        self._cursor_visible = True
        self._blink = QTimer(self)
        self._blink.timeout.connect(self._toggle_cursor)
        self._blink.start(500)

        self.find_query: str = ""
        self.replace_text: str = ""

        # highlight
        self.highlight_pos: Optional[Cursor] = None
        self.highlight_len: int = 0

    def _toggle_cursor(self):
        self._cursor_visible = not self._cursor_visible
        self.update()

    # -------- public API for main window --------
    def set_text(self, text: str):
        self.buf.set_text(text)
        self.cursor = Cursor(0, 0)
        self.undo.clear()
        self.update()

    def get_text(self) -> str:
        return self.buf.get_text()

    def open_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.set_text(f.read())

    def save_file(self, path: str):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.get_text())

    def do_undo(self):
        self.cursor = self.undo.undo(self.buf, self.cursor)
        self.cursor = self.buf.clamp_cursor(self.cursor)
        self.update()

    def do_redo(self):
        self.cursor = self.undo.redo(self.buf, self.cursor)
        self.cursor = self.buf.clamp_cursor(self.cursor)
        self.update()

    def set_find_replace(self, query: str, repl: str):
        self.find_query = query
        self.replace_text = repl

    def find_next(self):
        if not self.find_query:
            self.highlight_pos = None
            self.highlight_len = 0
            self.update()
            return
        
        found = self.buf.find_next(self.find_query, self.cursor)
        if found is not None:
            self.cursor = found
            self.highlight_pos = found.copy()
            self.highlight_len = len(self.find_query)
            self.highlight_pos.col = self.highlight_pos.col - self.highlight_len
        else:
            self.highlight_pos = None
            self.highlight_len = 0

        self.update()

    def replace_next(self):
        q = self.find_query
        r = self.replace_text
        if not q:
            return

        if not self.buf.replace_at(self.cursor, q, r):
            found = self.buf.find_next(q, self.buf.move_right(self.cursor))
            if found is None:
                return
            self.cursor = found
            found.col = found.col - len(q)

            if not self.buf.replace_at(self.cursor, q, r):
                self.update()
                return

        start = self.cursor.copy()
        end = Cursor(self.cursor.row, self.cursor.col + len(q))
        deleted = q

        self.buf.replace_at(self.cursor, r, q)  # revert
        self.cursor = self.undo.push_and_do(DeleteCommand(start, end, deleted), self.buf, self.cursor)
        self.cursor = self.undo.push_and_do(InsertCommand(start, r), self.buf, self.cursor)

        self.update()

    def replace_all(self, max_ops: int = 100000):
        q = self.find_query
        r = self.replace_text
        if not q:
            return

        c = Cursor(0, 0)
        ops = 0
        while ops < max_ops:
            found = self.buf.find_next(q, c)
            if found is None:
                break
            start = found
            end = Cursor(found.row, found.col + len(q))

            self.cursor = self.undo.push_and_do(DeleteCommand(start, end, q), self.buf, self.cursor)
            self.cursor = self.undo.push_and_do(InsertCommand(start, r), self.buf, self.cursor)

            c = Cursor(start.row, start.col + len(r))
            ops += 1

        self.cursor = self.buf.clamp_cursor(self.cursor)

        self.highlight_pos = None
        self.highlight_len = 0

        self.update()


    # rendering
    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setFont(self.font)

        rect = self.rect()
        painter.fillRect(rect, self.palette().base())

        x0 = self.padding
        y0 = self.padding + self.fm.ascent()

        # draw highlight
        if self.highlight_pos is not None and self.highlight_len > 0:
            hp = self.buf.clamp_cursor(self.highlight_pos.copy())
            row = hp.row
            line = self.buf.lines[row]

            start_col = max(0, min(hp.col, len(line)))
            end_col = max(0, min(hp.col + self.highlight_len, len(line)))

            if end_col > start_col:
                prefix = line[:start_col]
                marked = line[start_col:end_col]

                hx = x0 + self.fm.horizontalAdvance(prefix)
                hw = self.fm.horizontalAdvance(marked)
                hy = self.padding + row*self.line_h
                
                highlight_rect = QRect(hx, hy, max(1,hw), self.line_h)
                painter.fillRect(highlight_rect, self.palette().highlight())

        # draw lines
        for i, line in enumerate(self.buf.lines):
            y = y0 + i * self.line_h
            painter.drawText(x0, y, line)

        # draw cursor
        if self.hasFocus() and self._cursor_visible:
            cx = x0 + self.fm.horizontalAdvance(self.buf.lines[self.cursor.row][:self.cursor.col])
            cy_top = self.padding + self.cursor.row * self.line_h
            cursor_rect = QRect(cx, cy_top, max(2, self.char_w // 10 + 1), self.line_h)
            painter.fillRect(cursor_rect, self.palette().text())

        painter.end()


    # input handling
    def keyPressEvent(self, e: QKeyEvent):
        key = e.key()
        mods = e.modifiers()

        # shortcuts
        if mods & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Z:
                self.do_undo()
                return
            if key == Qt.Key.Key_Y:
                self.do_redo()
                return

        if key == Qt.Key.Key_Backspace:
            old = self.cursor.copy()
            new_cursor, deleted = self.buf.backspace_at(self.cursor, self.highlight_pos, self.highlight_len)
            if deleted:
                if deleted == "\n":
                    start = new_cursor
                    end = Cursor(new_cursor.row + 1, 0)
                else:
                    start = new_cursor
                    end = old
                self.buf.insert_text_at(start, deleted)
                self.cursor = self.undo.push_and_do(DeleteCommand(start, end, deleted), self.buf, self.cursor)
            else:
                self.cursor = new_cursor

            self.highlight_pos = None
            self.highlight_len = 0

            self.cursor = self.buf.clamp_cursor(self.cursor)
            self.update()
            return

        self.highlight_pos = None
        self.highlight_len = 0

        # navigation
        if key == Qt.Key.Key_Left:
            self.cursor = self.buf.move_left(self.cursor)
            self.update()
            return
        if key == Qt.Key.Key_Right:
            self.cursor = self.buf.move_right(self.cursor)
            self.update()
            return
        if key == Qt.Key.Key_Up:
            self.cursor = self.buf.move_up(self.cursor)
            self.update()
            return
        if key == Qt.Key.Key_Down:
            self.cursor = self.buf.move_down(self.cursor)
            self.update()
            return
        if key == Qt.Key.Key_Home:
            self.cursor = Cursor(self.cursor.row, 0)
            self.update()
            return
        if key == Qt.Key.Key_End:
            self.cursor = Cursor(self.cursor.row, len(self.buf.lines[self.cursor.row]))
            self.update()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cmd = InsertCommand(self.cursor, "\n")
            self.cursor = self.undo.push_and_do(cmd, self.buf, self.cursor)
            self.cursor = self.buf.clamp_cursor(self.cursor)
            self.update()
            return

        text = e.text()
        if text and text not in ("\n", "\r") and (mods == Qt.KeyboardModifier.NoModifier or mods == Qt.KeyboardModifier.ShiftModifier):
            cmd = InsertCommand(self.cursor, text)
            self.cursor = self.undo.push_and_do(cmd, self.buf, self.cursor)
            self.cursor = self.buf.clamp_cursor(self.cursor)
            self.update()
            return

        super().keyPressEvent(e)
