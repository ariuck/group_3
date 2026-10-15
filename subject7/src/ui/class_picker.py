"""Class 선택 (0~6) — 색 표시가 있는 클릭 줄 목록.

줄마다 'Class 색 네모 + 번호 + 이름' 이고, 고른 줄은 파란 바탕으로 강조한다. 사용 안 하는 Class 는 회색으로 보인다.

    picker = ClassPicker(부모, settings.CLASSES, on_pick=함수, columns=2)
    picker.set(3)        # 코드로 선택 (on_pick 은 부르지 않는다)
    picker.get()         # 지금 선택된 Class 번호
"""
import tkinter as tk

from src.ui import theme


class ClassPicker(tk.Frame):
    def __init__(self, parent, classes, on_pick, current=0, columns=2):
        super().__init__(parent, bg=theme.COLORS["card"])
        self._on_pick = on_pick
        self._current = current
        self._rows = {}                                   # Class 번호 → (줄, 색 네모, 이름 글자)
        rows_per_col = -(-len(classes) // columns)        # 올림
        for n, c in enumerate(classes):
            row = tk.Frame(self, bg=theme.COLORS["card"], cursor="hand2", padx=4, pady=1)
            row.grid(row=n % rows_per_col, column=n // rows_per_col, sticky="ew", padx=(0, 6), pady=0)
            chip = tk.Label(row, text=str(c["id"]), width=2, bg=c["color"] if c["enabled"] else theme.COLORS["faint"],
                            fg="#ffffff", font=theme.font(9, True))
            chip.pack(side="left")
            name = tk.Label(row, text=self._label(c), anchor="w", bg=theme.COLORS["card"],
                            fg=theme.COLORS["text"] if c["enabled"] else theme.COLORS["faint"], font=theme.font(10))
            name.pack(side="left", fill="x", expand=True, padx=(7, 0))
            for w in (row, chip, name):
                w.bind("<Button-1>", lambda e, cid=c["id"]: self._clicked(cid))
            self._rows[c["id"]] = (row, chip, name)
        for col in range(columns):
            self.columnconfigure(col, weight=1, uniform="cls")
        self.set(current)

    @staticmethod
    def _label(c):
        return c["name"].split(" (")[0] if c.get("name") else str(c["id"])

    def _clicked(self, cid):
        self._on_pick(cid)

    def set(self, cid):
        """선택 표시만 바꾼다 (on_pick 을 부르지 않는다)."""
        self._current = cid
        for key, (row, chip, name) in self._rows.items():
            sel = key == cid
            bg = theme.COLORS["accent_soft"] if sel else theme.COLORS["card"]
            row.config(bg=bg)
            name.config(bg=bg, font=theme.font(10, sel))

    def get(self):
        return self._current
