"""화면 아래 사진 목록(썸네일 줄).

현재 사진 주변의 미리보기 몇 장을 가로로 보여 주고, 누르면 그 사진으로 이동한다.
    · 창 너비에 맞춰 보이는 개수가 바뀐다.      · 현재 사진은 파란 테두리로 표시한다.
    · 사진 아래 글자에 저장 여부(✓)와 상태를 색으로 보여 준다.
    · 미리보기는 JPG 를 줄여서 읽고(draft) 한 번 읽은 것은 기억해 둔다. 아직 못 읽은 것은 회색 상자로 먼저 보여 주고
      가까운 것부터 하나씩 채워서, 방향키로 빠르게 넘길 때도 화면이 멈추지 않는다.

main_window 에서 쓰는 방법
    self.strip = ThumbStrip(self.root, on_select=self.on_thumb_selected, mark_of=self.thumb_mark)
    self.strip.set_files(paths)       # 폴더를 열었을 때
    self.strip.set_current(index)     # 사진이 바뀔 때
    self.strip.refresh_marks()        # 저장·상태가 바뀐 뒤
"""
import tkinter as tk
from collections import OrderedDict
from tkinter import ttk

from PIL import Image, ImageTk

THUMB_W, THUMB_H = 128, 72          # 미리보기 크기
CELL_PAD = 14                       # 칸 사이 여백(테두리 포함)
MAX_CELLS = 16                      # 만들어 두는 칸 수 (아주 넓은 화면에서도 충분)
CACHE_LIMIT = 150                   # 기억해 두는 미리보기 수
CURRENT_BG = "#1e88e5"
FONT = "Malgun Gothic"


def make_thumbnail(path, size=(THUMB_W, THUMB_H)):
    """JPG 미리보기 (PIL 이미지). 읽을 수 없으면 회색 상자."""
    try:
        im = Image.open(path)
        im.draft("RGB", (size[0] * 2, size[1] * 2))       # JPG 를 처음부터 작게 읽는다 (4K 도 빠름)
        im = im.convert("RGB")
        im.thumbnail(size)
        return im
    except Exception:  # noqa: BLE001 — 깨진 파일도 목록은 보여 주어야 한다
        return Image.new("RGB", size, "#999999")


class _Cell:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bd=2, relief="flat", padx=2, pady=1, cursor="hand2")
        self.pic = tk.Label(self.frame, width=THUMB_W, height=THUMB_H, padx=0, pady=0)
        self.pic.pack()
        self.cap = tk.Label(self.frame, font=(FONT, 8), width=22, anchor="center")
        self.cap.pack()
        self.index = None
        self.path = None


class ThumbStrip(tk.Frame):
    def __init__(self, parent, on_select, mark_of=None):
        super().__init__(parent)
        self._on_select = on_select
        self._mark_of = mark_of                      # mark_of(path) → (글자, 색)
        self.files = []
        self.current = -1
        self.start = 0
        self._cache = OrderedDict()                  # 경로 → PhotoImage
        self._marks = {}                             # 경로 → (글자, 색) — refresh_marks 때만 다시 계산한다
        self._queue = []
        self._job = None
        self._resize_job = None
        self._visible = 5
        self._blank = ImageTk.PhotoImage(Image.new("RGB", (THUMB_W, THUMB_H), "#cfcfcf"))

        # 윗줄: 제목 · 안내 · (main_window 가 버튼을 더할 수 있는 자리)
        self.header = tk.Frame(self)
        self.header.pack(fill="x")
        self.title = tk.Label(self.header, text="이미지 목록", font=(FONT, 9, "bold"))
        self.title.pack(side="left")
        self.hint = tk.Label(self.header, text="", fg="#666666", font=(FONT, 8))
        self.hint.pack(side="left", padx=8)

        # 아랫줄: ‹ [미리보기 ...] ›
        self.row = tk.Frame(self)
        self.row.pack(fill="x")
        self.btn_prev = ttk.Button(self.row, text="‹", width=2, command=lambda: self.page(-1), takefocus=False)
        self.btn_prev.pack(side="left")
        self.body = tk.Frame(self.row)
        self.body.pack(side="left", fill="x", expand=True)
        self.btn_next = ttk.Button(self.row, text="›", width=2, command=lambda: self.page(+1), takefocus=False)
        self.btn_next.pack(side="right")

        self.cells = []
        for k in range(MAX_CELLS):
            cell = _Cell(self.body)
            cell.pic.config(image=self._blank)           # 이미지를 넣어야 width/height 가 글자 수가 아닌 픽셀로 쓰인다
            for w in (cell.frame, cell.pic, cell.cap):
                w.bind("<Button-1>", lambda e, c=cell: self._clicked(c))
            self.cells.append(cell)
        self.bind("<Configure>", self._on_configure)

    # ── 바깥에서 쓰는 함수 ────────────────────────────────────────────────
    def set_files(self, files):
        """목록을 바꾼다 (폴더를 열었을 때). 이미 읽어 둔 미리보기는 그대로 쓴다."""
        self.files = list(files)
        self.current = -1
        self.start = 0
        self._marks.clear()
        self._update_title()
        self._refresh()

    def set_current(self, index):
        """현재 사진 번호(0부터). 보이는 범위를 벗어났으면 현재 사진이 보이도록 옮긴다."""
        self.current = index
        if not self._is_visible(index):
            self.start = self._start_for(index)
            self._refresh()
        else:
            self._style_cells()

    def refresh_marks(self):
        """저장·상태가 바뀐 뒤 글자(✓·상태)를 다시 계산해서 쓴다."""
        self._marks.clear()
        self._style_cells()

    def page(self, direction):
        """‹ › 버튼: 한 화면만큼 옮긴다 (현재 사진은 그대로)."""
        if not self.files:
            return
        n = self._visible
        self.start = max(0, min(self.start + direction * n, max(0, len(self.files) - n)))
        self._refresh()

    @property
    def visible_range(self):
        return self.start, min(len(self.files), self.start + self._visible)

    # ── 안쪽 ────────────────────────────────────────────────────────────
    def _update_title(self):
        self.title.config(text=f"이미지 목록 ({len(self.files)}개)")

    def _is_visible(self, index):
        return 0 <= index and self.start <= index < self.start + self._visible

    def _start_for(self, index):
        """index 가 가운데쯤 오도록 시작 위치를 정한다."""
        n = self._visible
        return max(0, min(index - n // 2, max(0, len(self.files) - n)))

    def _clicked(self, cell):
        if cell.index is not None:
            self._on_select(cell.index)

    def _on_configure(self, event):
        if event.widget is not self:
            return
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, self._fit_count)

    def _fit_count(self):
        """창 너비에 맞게 보이는 칸 수를 정한다."""
        self._resize_job = None
        usable = self.body.winfo_width() or (self.winfo_width() - 60)
        n = max(2, min(MAX_CELLS, usable // (THUMB_W + CELL_PAD)))
        if n != self._visible:
            self._visible = n
            if self.current >= 0 and not self._is_visible(self.current):
                self.start = self._start_for(self.current)
            self._refresh()

    def _refresh(self):
        """보이는 칸을 다시 채운다. 읽어 둔 미리보기는 바로, 아직 없는 것은 회색 상자 + 대기열."""
        self.start = max(0, min(self.start, max(0, len(self.files) - self._visible)))
        self._queue = []
        for k, cell in enumerate(self.cells):
            idx = self.start + k
            if k < self._visible and idx < len(self.files):
                cell.index, cell.path = idx, self.files[idx]
                if not cell.frame.winfo_ismapped():
                    cell.frame.pack(side="left", expand=True, fill="x", padx=3)
                photo = self._cache.get(cell.path)
                if photo is not None:
                    self._cache.move_to_end(cell.path)
                    cell.pic.config(image=photo)
                else:
                    cell.pic.config(image=self._blank)
                    self._queue.append(cell)
            else:
                cell.index = cell.path = None
                cell.frame.pack_forget()
        self._style_cells()
        center = self.current if self.current >= 0 else self.start
        self._queue.sort(key=lambda c: abs(c.index - center))        # 현재 사진에 가까운 것부터 채운다
        self._schedule_load()
        self.btn_prev.state(["!disabled" if self.start > 0 else "disabled"])
        self.btn_next.state(["!disabled" if self.start + self._visible < len(self.files) else "disabled"])

    def _style_cells(self):
        """현재 사진 강조 + 사진 아래 글자(저장 여부·상태)."""
        for cell in self.cells:
            if cell.index is None:
                continue
            is_cur = cell.index == self.current
            text, color = ("", "#333333")
            if self._mark_of is not None:
                if cell.path not in self._marks:
                    self._marks[cell.path] = self._mark_of(cell.path)
                text, color = self._marks[cell.path]
            name = cell.path.stem
            cell.cap.config(text=f"{name}\n{text}" if text else name, fg=color,
                            font=(FONT, 8, "bold" if is_cur else "normal"), height=2)
            bg = CURRENT_BG if is_cur else self.cget("bg")
            cell.frame.config(bg=bg)
            cell.cap.config(bg=bg, fg=("white" if is_cur else color))
            cell.pic.config(bg=bg)

    def _schedule_load(self):
        if self._queue and self._job is None:
            self._job = self.after(1, self._load_next)

    def _load_next(self):
        """미리보기를 한 장씩 읽는다 (한 번에 한 장 — 그 사이에 화면이 반응한다)."""
        self._job = None
        while self._queue:
            cell = self._queue.pop(0)
            if cell.path is None:
                continue
            path = cell.path
            photo = self._cache.get(path)
            if photo is None:
                photo = ImageTk.PhotoImage(make_thumbnail(path))
                self._cache[path] = photo
                while len(self._cache) > CACHE_LIMIT:
                    self._cache.popitem(last=False)
            if cell.path == path:                                    # 그 사이 다른 사진으로 바뀌지 않았으면
                cell.pic.config(image=photo)
            break
        self._schedule_load()

    def stop(self):
        """창을 닫을 때 예약된 작업을 정리한다."""
        for job in (self._job, self._resize_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        self._job = self._resize_job = None
