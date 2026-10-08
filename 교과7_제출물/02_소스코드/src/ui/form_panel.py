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
from src.ui import theme
from src.ui.hangul_input import HangulIME

SCENE_CHOICES = ["김치+대상 객체", "정상 김치", "대상 객체 단독", "판단 어려움"]   # docs/standards/manifest_guide.md 의 '이미지 유형' 값과 같게

# (검수표 머리글, 화면에 보이는 이름, 종류, 선택지, 값이 비었을 때 선택 버튼 이름)
FIELDS = [
    ("상태", "상태", "choice", STATUS_CHOICES, "자동"),
    ("이미지 유형", "이미지 유형", "choice", SCENE_CHOICES, "미정"),
    ("작성자", "작성자", "text", None, None),
    ("검수자", "검수자", "text", None, None),
    ("발견된 문제", "발견된 문제", "text", None, None),
    ("비고(수정 내용)", "비고", "text", None, None),
]
CHIP_COLUMNS = 3                      # 선택 버튼을 가로로 몇 개씩 펼칠지
REMEMBERED = ("작성자", "검수자")       # 직접 적으면 프로그램을 켜 둔 동안 기억하는 칸 (파일에는 저장하지 않는다)


class FormPanel(tk.Frame):
    """사람이 직접 채우는 칸을 모아 둔 카드. (선택 칸은 눌러서 고르는 칩, 글자 칸은 넓은 입력칸)"""

    def __init__(self, parent, on_change=None, on_mode=None, on_submit=None):
        C = theme.COLORS
        super().__init__(parent, bg=C["card"], highlightbackground=C["border"], highlightthickness=1, padx=12, pady=8)
        self._on_change = on_change
        self._on_mode = on_mode            # 한/영 상태가 바뀌었을 때 알림 (예: 상태줄에 안내)
        self._on_submit = on_submit        # 글자 칸에서 Enter 를 눌렀을 때 (예: 저장하고 다음 사진으로)
        self._loading = False
        self._remembered = {key: "" for key in REMEMBERED}     # 내가 마지막으로 직접 쓴 이름
        self._vars = {}
        self._entries = {}
        self._chips = {}                   # 선택 버튼 묶음(상태·이미지 유형) — 안내할 때 깜빡이게 하려고 기억
        self._flash_job = None
        self.ime = HangulIME(on_mode_change=self._show_mode)   # WSL 에서도 한글을 칠 수 있게 (hangul_input.py 참고)
        self.columnconfigure(0, weight=1)

        # 제목줄: '검수 기록' + 한/영 전환 버튼 (한/영 키·오른쪽 Alt·Shift+Space 로도 바뀐다)
        head = tk.Frame(self, bg=C["card"])
        head.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        tk.Label(head, text="검수 기록", bg=C["card"], fg=C["text"], font=theme.font(11, True)).pack(side="left")
        self._mode_btn = ttk.Button(head, width=11, command=self.ime.toggle, takefocus=False, style="Tool.TButton")
        self._mode_btn.pack(side="right")
        self._show_mode(self.ime.korean)
        row = 1

        for key, label, kind, choices, blank_label in FIELDS:
            if kind != "choice":
                continue
            var = tk.StringVar(value="")
            self._vars[key] = var
            tk.Label(self, text=label, bg=C["card"], fg=C["muted"], font=theme.font(9, True), anchor="w").grid(
                row=row, column=0, sticky="ew")
            chips = tk.Frame(self, bg=C["card"])
            chips.grid(row=row + 1, column=0, sticky="ew", pady=(2, 6))
            self._chips[key] = chips
            options = [(blank_label, "")] + [(c, c) for c in choices]
            for n, (text, value) in enumerate(options):
                ttk.Radiobutton(chips, text=text, value=value, variable=var, style="Chip.Toolbutton",
                                takefocus=False).grid(row=n // CHIP_COLUMNS, column=n % CHIP_COLUMNS, sticky="ew",
                                                      padx=(0 if n % CHIP_COLUMNS == 0 else 4, 0),
                                                      pady=(0 if n < CHIP_COLUMNS else 4, 0))
            for c in range(CHIP_COLUMNS):
                chips.columnconfigure(c, weight=1, uniform="chip")
            var.trace_add("write", self._changed)
            row += 2

        # 작성자 · 검수자는 한 줄에 나란히
        names = tk.Frame(self, bg=C["card"])
        names.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        for n, (key, label) in enumerate((("작성자", "작성자"), ("검수자", "검수자"))):
            tk.Label(names, text=label, bg=C["card"], fg=C["muted"], font=theme.font(9, True)).grid(
                row=0, column=n * 2, sticky="w", padx=(0 if n == 0 else 12, 6))
            var = tk.StringVar()
            entry = ttk.Entry(names, textvariable=var, width=10)
            entry.grid(row=0, column=n * 2 + 1, sticky="ew")
            names.columnconfigure(n * 2 + 1, weight=1)
            self.ime.attach(entry)
            entry.bind("<Return>", self._submit)
            var.trace_add("write", lambda *_a, k=key: self._typed(k))
            self._vars[key] = var
            self._entries[key] = entry
        row += 1

        for key, label in (("발견된 문제", "발견된 문제"), ("비고(수정 내용)", "비고")):
            tk.Label(self, text=label, bg=C["card"], fg=C["muted"], font=theme.font(9, True), anchor="w").grid(
                row=row, column=0, sticky="ew")
            var = tk.StringVar()
            entry = ttk.Entry(self, textvariable=var)
            entry.grid(row=row + 1, column=0, sticky="ew", pady=(2, 4))
            self.ime.attach(entry)
            entry.bind("<Return>", self._submit)
            var.trace_add("write", self._changed)
            self._vars[key] = var
            self._entries[key] = entry
            row += 2

    def _submit(self, _event):
        """글자 칸에서 Enter: 한글 조합 중인 글자를 확정하고 알려 준다."""
        self.ime.finish()
        if self._on_submit:
            self._on_submit()
        return "break"

    def focus_field(self, key, select_all=False):
        """검수 기록의 글자 칸(예: '발견된 문제')에 커서를 둔다. 맨 뒤로 가거나, select_all 이면 전체를 선택한다."""
        entry = self._entries.get(key)
        if entry is None:
            return False
        entry.focus_set()
        if select_all:
            entry.select_range(0, "end")
        else:
            entry.icursor("end")
        return True

    def choose_scene(self, index):
        """Ctrl+1~4: 이미지 유형을 번호로 고른다 (김치+대상 객체 / 정상 김치 / 대상 객체 단독 / 판단 어려움). 고른 값을 돌려준다."""
        value = SCENE_CHOICES[index]
        self._vars["이미지 유형"].set(value)
        return value

    def flash(self, key, ms=1600):
        """안내가 필요한 선택 칸(예: 이미지 유형)을 잠깐 빨간 테두리로 깜빡여 어디를 골라야 하는지 보여 준다."""
        chips = self._chips.get(key)
        if chips is None:
            return
        C = theme.COLORS
        if self._flash_job is not None:
            self.after_cancel(self._flash_job)
        chips.config(highlightbackground=C["danger"], highlightcolor=C["danger"], highlightthickness=3)
        self._flash_job = self.after(ms, lambda: self._unflash(chips))

    def _unflash(self, chips):
        self._flash_job = None
        try:
            chips.config(highlightthickness=0)
        except tk.TclError:
            pass

    def stop(self):
        """창을 닫을 때 깜빡임 예약을 정리한다."""
        if self._flash_job is not None:
            try:
                self.after_cancel(self._flash_job)
            except tk.TclError:
                pass
            self._flash_job = None

    def _show_mode(self, korean):
        self._mode_btn.config(text="한/영: 한글" if korean else "한/영: 영어")
        if self._on_mode:
            self._on_mode(korean)

    def _typed(self, key):
        """작성자·검수자 칸을 사람이 직접 고쳤다: 그 이름을 기억해 둔다. (불러오기·미리 채우기 중에는 기억을 바꾸지 않는다)"""
        if not self._loading:
            self._remembered[key] = self._vars[key].get().strip()
        self._changed()

    def fill_remembered(self):
        """비어 있는 작성자·검수자 칸에만 기억해 둔 이름을 미리 채운다. 이미 적힌 이름은 절대 바꾸지 않는다.

        - 작성자와 검수자는 달라야 하므로, 다른 쪽 칸에 이미 같은 이름이 있으면 채우지 않는다. (자기 사진을 자기가 검수하는 실수 방지)
        - 채운 것은 '사람이 고쳤다'로 보지 않는다. (저장 안 됨 표시가 뜨지 않는다. 저장할 때 검수표에 기록된다)
        """
        self._loading = True
        try:
            for key in REMEMBERED:
                name = self._remembered[key]
                other = self._vars["검수자" if key == "작성자" else "작성자"].get().strip()
                if name and not self._vars[key].get().strip() and other != name:
                    self._vars[key].set(name)
        finally:
            self._loading = False

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
