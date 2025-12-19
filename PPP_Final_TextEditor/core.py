from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class Cursor:
    row: int = 0
    col: int = 0

    def copy(self) -> "Cursor":
        return Cursor(self.row, self.col)


class TextBuffer:
    """
        리스트 기반 버퍼
        추후 최적화 고려할 것
    """
    # init
    def __init__(self, text: str=""):
        self.set_text(text)


    # getter/setter
    def set_text(self, text:str) -> None:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        self.lines: List[str] = text.split("\n")
        if len(self.lines) == 0:
            self.lines = [""]

    def get_text(self) -> str:
        return "\n".join(self.lines)


    # set text buffer's position 
    def clamp_cursor(self, c:Cursor) -> Cursor:
        c.row = max(0, min(c.row, len(self.lines)-1))
        c.col = max(0, min(c.col, len(self.lines[c.row])))
        return c
    
    # set cursor left char
    def move_left(self, c:Cursor) -> Cursor:
        c = c.copy()
        if c.col > 0:
            c.col -= 1
        elif c.row > 0:
            c.row -= 1
            c.col = len(self.lines[c.row])
        return c
    
    # set cursor right char
    def move_right(self, c:Cursor) -> Cursor:
        c = c.copy()
        if c.col < len(self.lines[c.row]):
            c.col += 1
        elif c.row < len(self.lines) - 1:
            c.row += 1
            c.col = 0
        return c
    
    # set cursor upper char
    def move_up(self, c:Cursor) -> Cursor:
        c = c.copy()
        if c.row > 0:
            c.row -= 1
            c.col = min(c.col, len(self.lines[c.row]))
        else:
            c.row = 0
            c.col = 0
        return c
    
    # set cursor lower char
    def move_down(self, c:Cursor) -> Cursor:
        c = c.copy()
        if c.row < len(self.lines) - 1:
            c.row += 1
            c.col = min(c.col, len(self.lines[c.row]))
        else:
            c.col = len(self.lines[c.row])
        return c
        

    # edit primitives
    def insert_text_at(self, pos:Cursor, text:str) -> Cursor:
        pos = self.clamp_cursor(pos.copy())
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        if text == "":
            return pos
        
        cur_line = self.lines[pos.row] 
        left = cur_line[:pos.col]
        right = cur_line[pos.col:]

        parts = text.split("\n")

        # single line
        if len(parts) == 1:
            self.lines[pos.row] = left + parts[0] + right
            return Cursor(pos.row, pos.col+len(parts[0]))
        
        # multi line
        first = left + parts[0]
        last = parts[-1] + right
        middle = parts[1:-1]

        self.lines[pos.row] = first
        insert_at = pos.row + 1
        for m in middle:
            self.lines.insert(insert_at, m)
            insert_at += 1
        self.lines.insert(insert_at, last)

        return Cursor(insert_at, len(parts[-1]))
    
    def delete_range(self, start:Cursor, end:Cursor) -> str:
        start = self.clamp_cursor(start.copy())
        end = self.clamp_cursor(end.copy())

        # single line
        if start.row == end.row:
            line = self.lines[start.row]
            deleted = line[start.col:end.col]
            self.lines[start.row] = line[:start.col]
            if len(line) > end.col: self.lines[start.row] = self.lines[start.row] + line[end.col:]
            return deleted
        
        # multi line
        first_line = self.lines[start.row]
        last_line = self.lines[end.row]
        deleted_lines = []

        deleted_lines.append(first_line[start.col:])
        for r in range(start.row+1, end.row):
            deleted_lines.append(self.lines[r])
        deleted_lines.append(last_line[:end.col])

        new_first = first_line[:start.col] + last_line[end.col:]
        del self.lines[start.row+1 : end.row+1]
        self.lines[start.row] = new_first

        return "\n".join(deleted_lines)

    def backspace_at(self, pos:Cursor, highlight_pos:Cursor, highlight_len:int) -> Tuple[Cursor,str]:
        if highlight_pos is not None and highlight_len > 0:
            start = highlight_pos.copy()
            end = highlight_pos.copy()
            end.col = end.col + highlight_len
            deleted = self.delete_range(start,end)
            return start,deleted

        pos = self.clamp_cursor(pos.copy())
        if pos.row==0 and pos.col==0:
            return pos,""
        
        if pos.col>0:
            start = Cursor(pos.row, pos.col-1)
            end = Cursor(pos.row, pos.col)
            deleted = self.delete_range(start, end)
            return start,deleted

        prev_row = pos.row-1
        prev_len = len(self.lines[prev_row])
        self.lines[prev_row] = self.lines[prev_row] + self.lines[pos.row]
        del self.lines[pos.row]
        return Cursor(prev_row, prev_len),"\n"

    def find_next(self, query:str, start:Cursor) -> Optional[Cursor]:
        if query=="":
            return None
            
        start = self.clamp_cursor(start.copy())

        line = self.lines[start.row]
        idx = line.find(query, start.col)
        if idx!=-1:
            return Cursor(start.row, idx+len(query))

        for r in range(start.row+1, len(self.lines)):
            idx = self.lines[r].find(query)
            if idx!=-1:
                return Cursor(r, idx+len(query))

        return None

    def replace_at(self, pos:Cursor, query:str, repl:str) -> bool:
        pos = self.clamp_cursor(pos.copy())
        if query=="":
            return False
        
        line = self.lines[pos.row]
        if line.startswith(query, pos.col):
            self.lines[pos.row] = line[:pos.col] + repl
            if len(line) > pos.col+len(query):
                self.lines[pos.row] = self.lines[pos.row] + line[pos.col+len(query):]
            return True
        
        return False



class Command:
    def do(self, buf:TextBuffer, cursor:Cursor) -> Cursor:
        raise NotImplementedError
    def undo(self, buf:TextBuffer, cursor:Cursor) -> Cursor:
        raise NotImplementedError


class InsertCommand(Command):
    def __init__(self, pos: Cursor, text: str):
        self.pos = pos.copy()
        self.text = text
        self.after: Optional[Cursor] = None

    def do(self, buf: TextBuffer, cursor: Cursor) -> Cursor:
        self.after = buf.insert_text_at(self.pos, self.text)
        return self.after.copy()

    def undo(self, buf: TextBuffer, cursor: Cursor) -> Cursor:
        if self.after is None:
            return cursor
        # delete inserted text range: [pos, after)
        deleted = buf.delete_range(self.pos, self.after)
        # safety: deleted should equal self.text normalized, but we don't enforce
        return self.pos.copy()


class DeleteCommand(Command):
    def __init__(self, start: Cursor, end: Cursor, deleted_text: str):
        self.start = start.copy()
        self.end = end.copy()
        self.deleted_text = deleted_text

    def do(self, buf: TextBuffer, cursor: Cursor) -> Cursor:
        # apply delete again
        buf.delete_range(self.start, self.end)
        return self.start.copy()

    def undo(self, buf: TextBuffer, cursor: Cursor) -> Cursor:
        return buf.insert_text_at(self.start, self.deleted_text)


class UndoStack:
    def __init__(self):
        self._undo: List[Command] = []
        self._redo: List[Command] = []

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def push_and_do(self, cmd: Command, buf: TextBuffer, cursor: Cursor) -> Cursor:
        new_cursor = cmd.do(buf, cursor)
        self._undo.append(cmd)
        self._redo.clear()
        return new_cursor

    def undo(self, buf: TextBuffer, cursor: Cursor) -> Cursor:
        if not self._undo:
            return cursor
        cmd = self._undo.pop()
        new_cursor = cmd.undo(buf, cursor)
        self._redo.append(cmd)
        return new_cursor

    def redo(self, buf: TextBuffer, cursor: Cursor) -> Cursor:
        if not self._redo:
            return cursor
        cmd = self._redo.pop()
        new_cursor = cmd.do(buf, cursor)
        self._undo.append(cmd)
        return new_cursor

