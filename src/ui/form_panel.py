"""입력칸 화면: 상태 · 작성자 · 검수자 · 이미지 유형 · 발견된 문제 · 비고.

여기서 받은 값은 manifest_writer.record_save(..., human=...) 로 검수표에 기록된다.
칸 이름은 검수표(dataset_manifest.csv) 머리글과 똑같다.

main_window 에서 쓰는 방법
    from src.ui.form_panel import FormPanel
    from src.manifest.manifest_writer import read_human, record_save

    self.form = FormPanel(오른쪽_패널, on_change=self._mark_dirty)
    self.form.pack(fill="x", padx=6, pady=6)

    # 이미지를 열 때: 검수표에 적혀 있던 값을 입력칸에 보여 준다
    self.form.set_values(read_human(image_path))

    # [저장] 할 때: TXT 저장이 끝난 뒤 입력칸 값을 함께 넘긴다
    msg = record_save(image_path, raw_txt, work_txt, screen_count, human=self.form.get_values())
    self.form.set_values(read_human(image_path))   # 프로그램이 정한 상태를 다시 보여 준다
"""
import tkinter as tk
from tkinter import ttk

from src.manifest.manifest_writer import STATUS_CHOICES
from src.ui.hangul_input import HangulIME

SCENE_CHOICES = ["김치+대상 객체", "정상 김치", "대상 객체 단독", "판단 어려움"]   # docs/manifest_guide.md 의 '이미지 유형' 값과 같게

# (검수표 머리글, 화면에 보이는 이름, 종류, 선택지)
FIELDS = [
    ("상태", "상태", "choice", STATUS_CHOICES),
    ("작성자", "작성자", "text", None),
    ("검수자", "검수자", "text", None),
    ("이미지 유형", "이미지 유형", "choice", SCENE_CHOICES),
    ("발견된 문제", "발견된 문제", "text", None),
    ("비고(수정 내용)", "비고", "text", None),
]


class FormPanel(ttk.LabelFrame):
    """사람이 직접 채우는 칸을 모아 둔 패널."""

    def __init__(self, parent, on_change=None):
        super().__init__(parent, text="검수 기록")
        self._on_change = on_change
        self._loading = False
        self._vars = {}
        self.ime = HangulIME(on_mode_change=self._show_mode)   # WSL 에서도 한글을 칠 수 있게 (hangul_input.py 참고)

        for row, (key, label, kind, choices) in enumerate(FIELDS):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=3)
            var = tk.StringVar()
            if kind == "choice":
                widget = ttk.Combobox(self, textvariable=var, values=[""] + list(choices), state="readonly", width=10)
            else:
                widget = ttk.Entry(self, textvariable=var, width=10)   # 좁게 시작하고 남는 폭만큼 늘어난다
                self.ime.attach(widget)
            widget.grid(row=row, column=1, sticky="ew", padx=6, pady=3)
            var.trace_add("write", self._changed)
            self._vars[key] = var

        # 한/영 전환 버튼 (한/영 키·오른쪽 Alt·Shift+Space 로도 바뀐다)
        self._mode_btn = ttk.Button(self, width=10, command=self.ime.toggle, takefocus=False)
        self._mode_btn.grid(row=len(FIELDS), column=1, sticky="e", padx=6, pady=(0, 3))
        self._show_mode(self.ime.korean)

        self.columnconfigure(1, weight=1)

    def _show_mode(self, korean):
        self._mode_btn.config(text="한/영: 한글" if korean else "한/영: 영어")

    def _changed(self, *_):
        # set_values 로 값을 채우는 동안에는 "사람이 고쳤다"로 보지 않는다.
        if not self._loading and self._on_change:
            self._on_change()

    def get_values(self):
        """입력칸 값을 {검수표 머리글: 값} 으로 돌려준다."""
        return {key: var.get().strip() for key, var in self._vars.items()}

    def set_values(self, row):
        """검수표의 한 줄(dict)을 입력칸에 채운다. 없는 값은 빈칸."""
        row = row or {}
        self._loading = True
        try:
            for key, var in self._vars.items():
                var.set(row.get(key) or "")
        finally:
            self._loading = False

    def clear(self):
        self.set_values({})
