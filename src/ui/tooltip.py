"""버튼 위에 마우스를 잠깐 올려 두면 뜨는 설명 말풍선.

    Tooltip(버튼, "Ctrl+S — 저장해요")
글자 대신 함수를 넘기면(Tooltip(버튼, lambda: ...)) 말풍선이 뜰 때마다 그 함수가 돌려준 글자를 보여 준다.
"""
import tkinter as tk

from src.ui import theme


class Tooltip:
    def __init__(self, widget, text, delay=550):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._job = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add=True)
        widget.bind("<Leave>", self._hide, add=True)
        widget.bind("<ButtonPress>", self._hide, add=True)
        widget.bind("<Destroy>", self._hide, add=True)

    def _schedule(self, _event=None):
        self._cancel()
        self._job = self.widget.after(self.delay, self.show)

    def _cancel(self):
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def show(self):
        self._job = None
        text = self.text() if callable(self.text) else self.text
        if not text or self._tip is not None:
            return
        try:
            x = self.widget.winfo_rootx() + 8
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
            tip = tk.Toplevel(self.widget)
            tip.wm_overrideredirect(True)                       # 제목줄 없는 작은 창
            tip.wm_geometry(f"+{x}+{y}")
            tk.Label(tip, text=text, justify="left", bg=theme.COLORS["text"], fg="#ffffff", font=theme.font(9),
                     padx=9, pady=5).pack()
            self._tip = tip
        except tk.TclError:                                     # 창이 이미 사라졌으면 조용히 넘어간다
            self._tip = None

    def _hide(self, _event=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None
