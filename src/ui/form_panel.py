"""입력칸 화면: 상태 · 이미지 유형 · 작성자 · 검수자 · 발견된 문제 · 비고.

여기서 받은 값은 manifest_writer.record_save(..., human=...) 로 검수표에 기록된다.
칸 이름은 검수표(dataset_manifest.csv) 머리글과 똑같다.

고르는 칸(상태·이미지 유형)은 목록을 펼쳐서 고르는 대신 라디오 버튼으로 한눈에 보이게 했다. (kimchi_labeling_v2 참고)
    상태        : 자동 / 검수 전 / 수정 완료 / 검수 완료 / 수정 필요 / 제외     ('자동' = 프로그램이 정함)
    이미지 유형 : 미정 / 김치+대상 객체 / 정상 김치 / 대상 객체 단독 / 판단 어려움

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

# (검수표 머리글, 화면에 보이는 이름, 종류, 선택지, 값이 비었을 때 라디오 이름)
FIELDS = [
    ("상태", "상태", "choice", STATUS_CHOICES, "자동"),
    ("이미지 유형", "이미지 유형", "choice", SCENE_CHOICES, "미정"),
    ("작성자", "작성자", "text", None, None),
    ("검수자", "검수자", "text", None, None),
    ("발견된 문제", "발견된 문제", "text", None, None),
    ("비고(수정 내용)", "비고", "text", None, None),
]
RADIO_COLUMNS = {"상태": 3, "이미지 유형": 2}      # 라디오를 가로로 몇 개씩 펼칠지


class FormPanel(ttk.Frame):
    """사람이 직접 채우는 칸을 모아 둔 패널."""

    def __init__(self, parent, on_change=None):
        super().__init__(parent, relief="groove", borderwidth=2, padding=2)
        self._on_change = on_change
        self._loading = False
        self._vars = {}
        self.ime = HangulIME(on_mode_change=self._show_mode)   # WSL 에서도 한글을 칠 수 있게 (hangul_input.py 참고)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # 제목줄: '검수 기록' + 한/영 전환 버튼 (한/영 키·오른쪽 Alt·Shift+Space 로도 바뀐다)
        head = ttk.Frame(self)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 2))
        ttk.Label(head, text="검수 기록", font=("Malgun Gothic", 10, "bold")).pack(side="left")
        self._mode_btn = ttk.Button(head, width=10, command=self.ime.toggle, takefocus=False)
        self._mode_btn.pack(side="right")
        self._show_mode(self.ime.korean)
        row = 1

        for key, label, kind, choices, blank_label in FIELDS:
            if kind != "choice":
                continue
            var = tk.StringVar(value="")
            self._vars[key] = var
            box = ttk.Frame(self)
            box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 2))
            ttk.Label(box, text=label, font=("Malgun Gothic", 9, "bold"), foreground="#444444").grid(
                row=0, column=0, columnspan=3, sticky="w")
            cols = RADIO_COLUMNS.get(key, 2)
            options = [(blank_label, "")] + [(c, c) for c in choices]
            for n, (text, value) in enumerate(options):
                ttk.Radiobutton(box, text=text, value=value, variable=var, takefocus=False).grid(
                    row=1 + n // cols, column=n % cols, sticky="w", padx=(2, 6))
            for c in range(cols):
                box.columnconfigure(c, weight=1)
            var.trace_add("write", self._changed)
            row += 1

        # 작성자 · 검수자는 한 줄에 나란히
        names = ttk.Frame(self)
        names.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
        for n, (key, label) in enumerate((("작성자", "작성자"), ("검수자", "검수자"))):
            ttk.Label(names, text=label).grid(row=0, column=n * 2, sticky="w", padx=(0 if n == 0 else 8, 3))
            var = tk.StringVar()
            entry = ttk.Entry(names, textvariable=var, width=8)
            entry.grid(row=0, column=n * 2 + 1, sticky="ew")
            names.columnconfigure(n * 2 + 1, weight=1)
            self.ime.attach(entry)
            var.trace_add("write", self._changed)
            self._vars[key] = var
        row += 1

        for key, label in (("발견된 문제", "발견된 문제"), ("비고(수정 내용)", "비고")):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=4)
            var = tk.StringVar()
            entry = ttk.Entry(self, textvariable=var, width=10)
            entry.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
            self.ime.attach(entry)
            var.trace_add("write", self._changed)
            self._vars[key] = var
            row += 1

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
        """검수표의 한 줄(dict)을 입력칸에 채운다. 없는 값은 빈칸(라디오는 '자동'·'미정')."""
        row = row or {}
        self._loading = True
        try:
            for key, var in self._vars.items():
                var.set(row.get(key) or "")
        finally:
            self._loading = False

    def clear(self):
        self.set_values({})
