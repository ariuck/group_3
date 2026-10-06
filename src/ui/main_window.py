"""라벨링 화면 (Tkinter) — 이미지 1장 End-to-End.

    [데이터 조사]  → 실제 JPG / TXT 구조 · 개수 · 짝(Pair) · Class 분포를 조사
    [이미지 열기]  → 같은 이름의 TXT 자동 Load → BBox 표시
    BBox 추가 / 삭제 / Class 변경
    [저장]         → WORK 폴더에 "RAW 와 같은 구조"로 저장  (RAW 는 절대 수정하지 않음)
                        + 오른쪽 '검수 기록' 입력칸(상태·작성자·검수자 등)을 검수표(CSV)에 함께 기록
    [다시 불러오기] → 같은 위치에 BBox 가 복원되는지 확인
    ③ Zoom·편집      → 마우스 휠 확대/축소 · 오른쪽(또는 휠) 버튼 드래그 이동 · F = 화면 맞춤
                        Ctrl+Z 되돌리기 · Ctrl+Y 다시 실행

[핵심 약속] BBox 는 "화면 좌표"가 아니라 "원본 이미지 픽셀 좌표"로 기억한다.
            화면에 그릴 때만 배율(scale)을 곱하고, 마우스 입력은 배율로 나눠서 되돌린다.
            확대·이동 계산은 src/bbox/viewport.py (Viewport) 가 맡는다.

[Tkinter 6대 개념이 나오는 곳]
   변수 → self.boxes, self.vp ...         위젯 → Canvas, Button, Listbox, Label
   이벤트 bind → canvas.bind(...)         명령 command → Button(command=...)
   함수 → open_image(), save() ...        mainloop → 맨 아래 main()

기능별 코드는 따로 나뉘어 있다:  src/yolo (TXT 읽기·쓰기·좌표) · src/bbox (BBox 만들기·선택·확대·Undo) ·
src/validation (데이터 조사) · src/data_paths (RAW/WORK 경로) · src/settings (경로·Class 설정)
"""
import math
import os
import shutil
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageEnhance, ImageTk   # Pillow: JPG 를 읽고 화면용으로 줄이는 데 사용

from src import settings
from src.bbox.bbox_diff import diff_boxes, diff_summary
from src.bbox.bbox_edit import HANDLE_CURSORS, handle_points, hit_handle, move_box, resize_box
from src.bbox.bbox_manager import MIN_DRAG_PX, box_problems, find_box_at, make_box
from src.bbox.history import History
from src.bbox.viewport import ZOOM_STEP, Viewport
from src.data_paths import find_raw_image, is_inside, locate_in_raw, work_label_path
from src.manifest.manifest_writer import (STATUS_DONE, STATUS_EDITED, STATUS_REVIEW, ManifestError, read_human,
                                          read_status_map, record_save, status_of)
from src.ui.folder_drop import make_root, pick_target, register_drop
from src.ui.form_panel import FormPanel
from src.ui import theme
from src.ui.class_picker import ClassPicker
from src.ui.help_dialog import show_shortcuts
from src.ui.tooltip import Tooltip
from src.ui.session import load_session, save_session
from src.ui.thumb_strip import ThumbStrip
from src.ui.validation_dialog import show_validation_dialog
from src.validation.validator import inventory_markdown, scan_inventory, validate_dataset, write_report
from src.yolo.coords import pixel_to_yolo
from src.yolo.yolo_loader import find_raw_label, read_yolo_file
from src.yolo.yolo_writer import write_yolo_file
from src.ui.navigator import ImageNavigator


class Day1Labeler:
    def __init__(self, root):
        self.root = root
        root.title("교과 7 · 이미지 라벨링 (RAW / WORK 구조)")
        theme.setup(root)                                       # 색·글꼴·버튼 모양 (src/ui/theme.py)
        root.geometry(f"1520x{min(960, root.winfo_screenheight() - 80)}")      # 화면이 작으면 높이를 줄인다
        root.minsize(1280, 820)                                                 # 이보다 작으면 버튼·패널이 잘린다

        # ------------------------------------------------------------------
        # [Tkinter 개념 1: 변수]  프로그램이 '기억해야 하는 것'들
        # ------------------------------------------------------------------
        self.image_path = None     # 지금 열려 있는 이미지 경로
        self.pil_image = None      # 원본 이미지 (PIL).  4K 라도 원본은 그대로 보관
        self.img_w = 0             # 원본 가로 픽셀
        self.img_h = 0             # 원본 세로 픽셀

        self.boxes = []            # ★ BBox 목록. 모든 좌표는 '원본 이미지 픽셀' 기준
        self.selected = None       # 선택된 BBox 번호 (없으면 None)
        self.current_class = 0     # 새 BBox 를 만들 때 쓸 Class
        self.dirty = False         # 저장 안 한 변경이 있는가?
        self._load_state = None    # 방향키 이동 중 다른 스레드에서 읽고 있는 사진 {경로, 결과, 끝났는지, ...}
        self.manifest_ok = True    # 이 사진의 검수 기록을 읽었는가 (못 읽었으면 경고 줄에 계속 표시)
        self._manifest_warned = "ok"   # 검수표를 못 읽어 경고를 이미 보여 준 파일의 수정 시각 (같은 파일에 경고창을 반복하지 않는다)
        self._edit_serial = 0      # BBox·검수 기록을 고칠 때마다 1 증가 — 사진을 읽는 동안 편집했는지 알아내는 데 쓴다
        self._nav_serial = 0       # 방향키 이동을 시작할 때의 편집 횟수
        self._load_seq = 0         # 사진을 화면에 올릴 때마다 1 증가 — 읽는 동안 다른 사진이 열렸으면 그 결과를 버리는 데 쓴다
        self._poll_job = None
        self._status_hold_until = 0.0   # 이 시각까지는 결과 메시지를 좌표 안내로 덮지 않는다
        self._nudge_idx, self._nudge_t = None, 0.0   # 키보드 미세 이동: 직전에 움직인 BBox 와 시각 (연속 이동을 Undo 한 번으로 묶는다)
        self.unreadable = 0        # 원본 라벨에서 형식이 맞지 않아 읽지 못한 줄 수 (저장하면 WORK 파일에서 빠진다)
        self._unreadable_ok = None  # 그래도 저장하겠다고 확인한 사진 (같은 사진은 다시 묻지 않는다)
        self._clean = []           # 마지막으로 불러오거나 저장한 BBox 목록 (Undo 후 '변경 없음' 판단용)

        self.vp = Viewport()       # ★ 화면 = 원본 × scale + offset  (확대·이동 상태를 모두 여기서 관리)
        self.auto_fit = True       # True 면 창 크기가 바뀔 때 다시 '화면 맞춤'. 사용자가 확대/이동하면 False
        self.history = History()   # Undo / Redo 기록
        self.photo = None          # 화면에 그릴 이미지 (ImageTk). 변수에 꼭 붙들고 있어야 사라지지 않는다!

        self.drag = None           # 드래그 중인 정보 (시작점, 임시 사각형 등)
        self.pan_last = None       # 화면 이동(오른쪽 드래그) 중 마지막 마우스 위치
        self._cursor = "crosshair"  # 지금 캔버스 마우스 모양 (바뀔 때만 다시 지정)
        self._listed_files = None  # 하단 사진 목록에 올려 둔 사진들 (폴더가 바뀔 때만 다시 올린다)
        self._status_cache = (object(), {})   # (검수표 수정 시각, {사진: 상태}) — 사진 목록 글자용
        self._summary_key, self._summary_text = None, ""   # 작업 진행 요약 (검수표·목록이 바뀔 때만 다시 센다)
        self.raw_boxes = []        # 이 사진의 원본(RAW) BBox — Diff 보기에서 지금 BBox 와 비교한다
        self.bright_idx = 0        # 화면 보정(밝기·대비·흑백) — 화면에 보이는 모습만 바꾼다. 원본 사진과 저장 파일은 그대로
        self.contrast_idx = 0
        self.gray = False
        self._resize_job = None    # 창 크기 변경 후 다시 그리기 예약(디바운스)용
        self._render_job = None    # 화면 이동 중 이미지 다시 그리기 예약용

        self.navigator = ImageNavigator() # 네비게이터 추가
        self._nav_pending = None   # ← → 를 누르는 동안 '가려는 사진 번호' (아직 화면에 안 올린 것)
        self._nav_job = None       # 그 사진을 읽도록 예약한 작업

        self.build_widgets()
        self.bind_events()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_image()
        self.set_status(self.start_message())
        self._restore_job = self.root.after(150, self.restore_session)   # 창이 뜬 직후, 마지막으로 보던 폴더·사진을 다시 연다

    # 예전 코드·설명과의 호환용: self.scale / offset_x / offset_y 는 Viewport 값을 그대로 보여 준다.
    @property
    def scale(self):
        return self.vp.scale

    @property
    def offset_x(self):
        return self.vp.offset_x

    @property
    def offset_y(self):
        return self.vp.offset_y

    def start_message(self):
        """처음 화면에 보여 줄 안내. 데이터가 아직 없으면 어디에 넣어야 하는지 알려 준다."""
        raw = settings.RAW_DIR
        if raw.is_dir() and any(raw.rglob("*.jpg")):
            return "[폴더 열기]로 폴더를 열거나 [이미지 열기]로 사진 1장을 열어 보세요.   (F1 = 단축키 도움말 · 도구 ▸ 데이터 조사에서 개수와 짝 확인)"
        return "data/raw 폴더에 데이터가 없습니다.  이물검출_학습데이터1·2 의 images / labels 파일을 data/raw 안에 넣어 주세요."

    # ------------------------------------------------------------------
    # 화면 만들기 ([Tkinter 개념 2: 위젯] + [개념 4: command])
    # ------------------------------------------------------------------
    def build_widgets(self):
        C = theme.COLORS
        # ① 위쪽 도구 줄 — 같은 일을 하는 버튼끼리 묶고, 주요 버튼(저장)은 파랑으로 강조한다.
        #    command=... 에는 '누르면 실행할 함수'를 연결한다. (괄호 없이 함수 이름만! 괄호를 붙이면 지금 바로 실행돼 버린다)
        bar = ttk.Frame(self.root, style="Bar.TFrame", padding=(14, 9))
        bar.pack(side="top", fill="x")
        tk.Frame(self.root, height=1, bg=C["border"]).pack(side="top", fill="x")      # 도구 줄 아래 구분선
        self.pan_var = tk.BooleanVar(value=False)
        groups = [  # (글자, 할 일, 모양)
            [("이미지 열기", self.open_image, "Tool"), ("폴더 열기", self.open_folder, "Tool")],
            [("저장", self.save, "Primary"), ("저장+다음", self.save_and_next, "Soft")],
            [("↶ 되돌리기", self.undo, "Tool"), ("↷ 다시", self.redo, "Tool"), ("삭제", self.delete_selected, "Danger"),
             ("전체 삭제", self.clear_all, "Danger")],
            [("⤢ 맞춤", self.fit_to_window, "Tool"), ("－", self.zoom_out, "Tool"), ("＋", self.zoom_in, "Tool"), "PAN"],
            ["TOOLS"],
        ]
        for gi, group in enumerate(groups):
            if gi:
                ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=10, pady=2)
            for item in group:
                if item == "TOOLS":               # 자주 쓰지 않는 도구는 메뉴 하나로 묶는다
                    menu = tk.Menu(self.root, tearoff=0, bg=C["card"], fg=C["text"], activebackground=C["accent_soft"],
                                   activeforeground=C["text"], font=theme.font(10), borderwidth=1, relief="solid")
                    for text, func in (("데이터 조사", self.show_inventory), ("QA 검증 (무결성)", self.run_validation),
                                       ("다시 불러오기", self.reload), ("WORK 폴더 열기", self.open_work_folder)):
                        menu.add_command(label=text, command=func)
                    menu.add_separator()
                    menu.add_command(label="단축키 도움말 (F1)", command=self.show_help)
                    ttk.Menubutton(bar, text="도구", menu=menu, style="Tool.TMenubutton", takefocus=False).pack(
                        side="left", padx=3)
                elif item == "PAN":               # 켜 두면 왼쪽 버튼 드래그로도 화면을 옮긴다 (오른쪽 버튼이 불편할 때)
                    chip = ttk.Checkbutton(bar, text="이동 모드", variable=self.pan_var, style="Chip.Toolbutton",
                                           command=self.on_pan_toggled, takefocus=False)
                    chip.pack(side="left", padx=3)
                    Tooltip(chip, self.TOOLTIPS["이동 모드"])
                else:
                    btn = ttk.Button(bar, text=item[0], command=item[1], style=f"{item[2]}.TButton", takefocus=False)
                    btn.pack(side="left", padx=3)
                    if item[0] in self.TOOLTIPS:
                        Tooltip(btn, self.TOOLTIPS[item[0]])
        self.zoom_label = ttk.Label(bar, text="100%", style="Bar.TLabel", font=theme.font(11, True), width=6,
                                    anchor="e")
        self.zoom_label.pack(side="right")

        # ② 가운데 영역(이미지 쪽) — 보기 옵션 줄 + 머리글 + 도화지 + 좌표줄 + 사진 목록. (pack 은 맨 마지막에)
        center = ttk.Frame(self.root, padding=(14, 10, 12, 8))
        opts = ttk.Frame(center, padding=(0, 0, 0, 8))          # 보기 옵션 줄 (Diff · 십자선 · 밝기·대비·흑백)
        opts.pack(side="top", fill="x")
        self.opts_bar = opts
        self.tools = opts
        ttk.Label(opts, text="보기", style="Muted.TLabel").pack(side="left", padx=(0, 10))
        self.diff_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="RAW 와 비교(Diff)", variable=self.diff_var, command=self.on_diff_toggled,
                        takefocus=False).pack(side="left")
        self.show_boxes_var = tk.BooleanVar(value=True)           # 끄면 BBox 를 숨겨 아래의 이물을 그대로 볼 수 있다 (H 키)
        ttk.Checkbutton(opts, text="BBox 보기", variable=self.show_boxes_var, command=self.on_boxes_toggled,
                        takefocus=False).pack(side="left", padx=(10, 0))
        self.cross_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="십자선", variable=self.cross_var, command=self.on_cross_toggled,
                        takefocus=False).pack(side="left", padx=(10, 0))
        ttk.Separator(opts, orient="vertical").pack(side="left", fill="y", padx=12, pady=2)
        self.btn_bright = ttk.Button(opts, text="밝기 ×1.0", command=self.cycle_brightness, style="Tool.TButton",
                                     takefocus=False)
        self.btn_bright.pack(side="left", padx=(0, 4))           # 어두운 사진의 작은 이물을 찾을 때 (화면에만 적용)
        self.btn_contrast = ttk.Button(opts, text="대비 ×1.0", command=self.cycle_contrast, style="Tool.TButton",
                                       takefocus=False)
        self.btn_contrast.pack(side="left", padx=(0, 4))
        self.gray_var = tk.BooleanVar(value=False)
        self.btn_gray = ttk.Checkbutton(opts, text="흑백", variable=self.gray_var, style="Chip.Toolbutton",
                                        command=self.on_gray_clicked, takefocus=False)
        self.btn_gray.pack(side="left")
        self.diff_label = ttk.Label(opts, text="", style="Diff.TLabel")
        self.diff_label.pack(side="left", padx=(16, 0))          # Diff 를 켜면 '추가 N · 수정 N · 삭제 N · 그대로 N'

        # ③ 맨 아래 상태줄 (창 전체 폭). 먼저 pack 해야 창이 작아져도 안 가려진다
        self.status = ttk.Label(self.root, text="", style="Status.TLabel", padding=(14, 5), anchor="w")
        self.status.pack(side="bottom", fill="x")

        # ④ 오른쪽 패널: 카드 3장 — 클래스 / 라벨 목록 / 검수 기록  (창 전체 높이를 쓴다)
        side = ttk.Frame(self.root, width=420, padding=(0, 6, 14, 10))
        side.pack(side="right", fill="y")
        side.pack_propagate(False)       # 안의 내용 크기에 맞춰 줄어들지 않고 폭 420 유지

        cls_card = theme.card(side, padx=12, pady=8)
        cls_card.pack(fill="x", pady=(0, 8))
        head = tk.Frame(cls_card, bg=C["card"])
        head.pack(fill="x", pady=(0, 4))
        tk.Label(head, text="클래스", bg=C["card"], fg=C["text"], font=theme.font(11, True)).pack(side="left")
        tk.Label(head, text="숫자키 0~6 으로도 고를 수 있어요", bg=C["card"], fg=C["muted"], font=theme.font(9)).pack(
            side="left", padx=(8, 0))
        self.class_list = ClassPicker(cls_card, settings.CLASSES, on_pick=self.choose_class, current=self.current_class)
        self.class_list.pack(fill="x")

        # 검수 기록 입력칸 — 패널 맨 아래에 둔다 (라벨 목록보다 먼저 pack 해야 창이 작아져도 안 가려진다)
        self.form = FormPanel(side, on_change=self.on_form_changed, on_mode=self.on_ime_mode, on_submit=self.on_form_submit)
        self.form.ime.bind_global(self.root)             # 한/영 키는 이미지 화면에 커서가 있어도 바뀐다
        self.form.pack(side="bottom", fill="x", pady=(8, 0))

        box_card = theme.card(side, padx=12, pady=8)
        box_card.pack(fill="both", expand=True)
        self.box_title = tk.Label(box_card, text="라벨 목록 (0개)", bg=C["card"], fg=C["text"], font=theme.font(11, True),
                                  anchor="w")
        self.box_title.pack(fill="x", pady=(0, 4))
        self.box_list = ttk.Treeview(box_card, columns=("no", "cls", "pos", "state"), show="headings", height=3,
                                     selectmode="browse")
        for col, text, width, anchor in (("no", "No", 36, "center"), ("cls", "클래스", 150, "w"),
                                         ("pos", "위치 (x,y,w,h)", 140, "w"), ("state", "상태", 52, "center")):
            self.box_list.heading(col, text=text)
            self.box_list.column(col, width=width, anchor=anchor, stretch=(col == "pos"))
        self.box_list.tag_configure("changed", foreground=C["warn"])        # 내가 고치거나 추가한 BBox 는 주황
        self.box_list.tag_configure("problem", foreground=C["danger"])      # 이미지 밖·Class 범위 밖 등 이상한 BBox 는 빨강
        self.box_list.pack(fill="both", expand=True)
        self._box_guard = False                                              # 표를 다시 채우는 동안 선택 이벤트를 무시

        # ⑤ 가운데: 머리글(파일 이름 · 번호 이동) + 이미지 도화지 + 좌표줄 + 사진 목록
        center.pack(side="left", fill="both", expand=True)       # (상태줄·오른쪽 패널을 먼저 pack 한 뒤 남는 자리를 차지)
        row = ttk.Frame(center)
        row.pack(side="top", fill="x", pady=(0, 8))
        titles = ttk.Frame(row)
        titles.pack(side="left", fill="x", expand=True)
        name_row = ttk.Frame(titles)
        name_row.pack(anchor="w")
        self.info = ttk.Label(name_row, text="사진을 열어 주세요", style="Title.TLabel")
        self.info.pack(side="left")
        self.dirty_label = ttk.Label(name_row, text="", style="Dirty.TLabel")      # 저장하지 않은 변경이 있으면 눈에 띄게
        self.dirty_label.pack(side="left", padx=(12, 0))
        self.info_meta = ttk.Label(titles, text="", style="Muted.TLabel")
        self.info_meta.pack(anchor="w")
        self.warn_label = ttk.Label(titles, text="", style="Warn.TLabel")      # 읽지 못한 줄 · 이상한 BBox 경고 (사라지지 않고 계속 보인다)
        self.warn_label.pack(anchor="w")
        self.btn_next = ttk.Button(row, text="다음 ▶", command=self.go_next, style="Tool.TButton", state="disabled",
                                   takefocus=False)
        self.btn_next.pack(side="right", padx=(4, 0))
        self.btn_jump = ttk.Button(row, text="이동", command=self.jump_to_entered_index, style="Tool.TButton",
                                   takefocus=False)
        self.btn_jump.pack(side="right", padx=(4, 0))
        self.total_label = ttk.Label(row, text="/ 0", style="Muted.TLabel", font=theme.font(11))
        self.total_label.pack(side="right", padx=(4, 2))
        self.entry_index = ttk.Entry(row, width=5, justify="center", style="Nav.TEntry", font=theme.font(11, True))
        self.entry_index.pack(side="right")                      # 사진 번호를 직접 입력
        self.entry_index.insert(0, "0")
        self.entry_index.bind("<Return>", lambda e: self.jump_to_entered_index())
        self.entry_index.bind("<KP_Enter>", lambda e: self.jump_to_entered_index())
        self.entry_index.bind("<FocusIn>", lambda e: self.entry_index.select_range(0, "end"))
        self.entry_index.bind("<Escape>", lambda e: (self.show_nav_number(self.navigator.index + 1 if self.navigator.index >= 0 else 0),
                                                     self.canvas.focus_set()))
        self.btn_prev = ttk.Button(row, text="◀ 이전", command=self.go_prev, style="Tool.TButton", state="disabled",
                                   takefocus=False)
        self.btn_prev.pack(side="right", padx=(0, 6))
        Tooltip(self.btn_prev, "← 또는 A 또는 PageUp")
        Tooltip(self.btn_next, "→ 또는 D 또는 PageDown")
        Tooltip(self.entry_index, "사진 번호를 입력하고 Enter — Ctrl+G 로 바로 이 칸으로 올 수 있어요")

        # 아래부터 쌓는다: 사진 목록(맨 아래) → 좌표줄 → (남는 자리) 도화지
        self.strip = ThumbStrip(center, on_select=self.on_thumb_selected, mark_of=self.thumb_mark)
        self.strip.pack(side="bottom", fill="x", pady=(8, 0))
        self.bbox_info = ttk.Label(center, text="", style="Coord.TLabel", padding=(2, 6), anchor="w")
        self.bbox_info.pack(side="bottom", fill="x")

        # 보기 필터: 상태별로 걸러서 본다 (예: '수정 필요' 인 사진만) — 사진 목록 제목줄 오른쪽
        self.filter_var = tk.StringVar(value=self.FILTER_ALL)
        self.filter_box = ttk.Combobox(self.strip.header, textvariable=self.filter_var, values=self.FILTER_CHOICES,
                                       state="readonly", width=16, takefocus=False)
        self.filter_box.pack(side="right")
        tk.Label(self.strip.header, text="보기", bg=C["card"], fg=C["muted"], font=theme.font(9)).pack(side="right", padx=(0, 6))
        self.filter_box.bind("<<ComboboxSelected>>", lambda e: (self.on_filter_changed(), self.canvas.focus_set()))

        view = tk.Frame(center, bg=C["border"], padx=1, pady=1)  # 도화지 둘레 옅은 테두리
        view.pack(side="top", fill="both", expand=True)
        self.canvas = tk.Canvas(view, bg=C["canvas"], highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        # 폴더·사진을 창에 끌어다 놓기 (tkinterdnd2 가 있을 때만)
        register_drop(self.root, self.on_drop)                   # (안내 문구는 빈 화면 가운데에 이미 있어서 제목줄에는 두지 않는다)

    # ------------------------------------------------------------------
    # 이벤트 연결 ([Tkinter 개념 3: 이벤트 bind])
    #   "어떤 일이 생기면(이벤트) → 어떤 함수를 실행할까" 를 연결해 두는 것
    # ------------------------------------------------------------------
    def bind_events(self):
        c = self.canvas
        c.bind("<ButtonPress-1>", self.on_mouse_down)       # 왼쪽 버튼을 누른 순간
        c.bind("<B1-Motion>", self.on_mouse_drag)           # 누른 채로 움직이는 동안
        c.bind("<ButtonRelease-1>", self.on_mouse_up)       # 버튼을 뗀 순간
        c.bind("<Motion>", self.on_mouse_move)              # 그냥 움직일 때 (좌표 표시용)
        c.bind("<Leave>", lambda e: self.canvas.delete("cross"))   # 마우스가 캔버스를 벗어나면 십자선을 지운다
        c.bind("<Configure>", self.on_canvas_resize)        # 도화지 크기가 바뀔 때

        # ③ 확대 / 이동
        c.bind("<MouseWheel>", self.on_mouse_wheel)         # Windows · macOS 휠
        c.bind("<Button-4>", self.on_mouse_wheel)           # Linux(WSL 포함) 휠 위
        c.bind("<Button-5>", self.on_mouse_wheel)           # Linux(WSL 포함) 휠 아래
        c.bind("<Enter>", lambda e: c.focus_set())          # 마우스가 들어오면 휠 입력을 캔버스가 받도록
        for btn in (2, 3):                                  # 휠 버튼(2) · 오른쪽 버튼(3) 드래그 = 화면 이동
            c.bind(f"<ButtonPress-{btn}>", self.on_pan_start)
            c.bind(f"<B{btn}-Motion>", self.on_pan_drag)
            c.bind(f"<ButtonRelease-{btn}>", self.on_pan_end)

        self.box_list.bind("<<TreeviewSelect>>", self.on_box_list_selected)

        r = self.root
        # 입력칸에 글자를 치는 중에는 글자·숫자 단축키가 동작하면 안 된다
        # (비고에 'f'·'-'·'3' 을 쳤는데 화면이 맞춰지거나 축소되거나 Class 가 바뀌면 안 됨)
        r.bind("<Delete>", lambda e: None if self.is_typing(e) else self.delete_selected())
        r.bind("<Control-s>", lambda e: self.save())
        r.bind("<Escape>", lambda e: None if self.is_typing(e) else self.on_escape())
        for key in ("w", "W"):                              # W = 저장 후 다음 사진
            r.bind(key, lambda e: None if self.is_typing(e) else self.save_and_next())
        r.bind("<Control-z>", lambda e: None if self.is_typing(e) else self.undo())
        r.bind("<Control-y>", lambda e: None if self.is_typing(e) else self.redo())
        r.bind("<Control-Z>", lambda e: None if self.is_typing(e) else self.redo())        # Ctrl+Shift+Z
        for key in ("<plus>", "<equal>", "<KP_Add>"):
            r.bind(key, lambda e: None if self.is_typing(e) else self.zoom_in())
        for key in ("<minus>", "<KP_Subtract>"):
            r.bind(key, lambda e: None if self.is_typing(e) else self.zoom_out())
        for key in ("f", "F", "<Control-Key-0>"):           # 숫자 0 은 Class 0 이라 F / Ctrl+0 을 화면 맞춤으로 쓴다
            r.bind(key, lambda e: None if self.is_typing(e) else self.fit_to_window())
        for i in range(len(settings.CLASSES)):              # 숫자키 0~6 = Class 선택
            r.bind(str(i), lambda e, cid=i: None if self.is_typing(e) else self.choose_class(cid))
        # ← → / PageUp·PageDown / A·D = 이전/다음 사진 (입력칸에서 글자를 치는 중에는 사진이 넘어가면 안 된다)
        for key in ("<Left>", "<Prior>", "a", "A"):                     # Prior/Next = PageUp/PageDown
            r.bind(key, lambda e: None if self.is_typing(e) else self.go_prev())
        for key in ("<Right>", "<Next>", "d", "D"):
            r.bind(key, lambda e: None if self.is_typing(e) else self.go_next())

        # 한 키 검수: Enter = 이상 없음(검수 완료) 후 다음 · R = 수정 필요로 표시 · N = 아직 안 한 사진으로
        r.bind("<Return>", lambda e: None if self.is_typing(e) else self.mark_ok_and_next())
        r.bind("<KP_Enter>", lambda e: None if self.is_typing(e) else self.mark_ok_and_next())
        for key in ("r", "R"):
            r.bind(key, lambda e: None if self.is_typing(e) else self.mark_review())
        for key in ("n", "N"):
            r.bind(key, lambda e: None if self.is_typing(e) else self.go_next_unworked())

        # BBox 키보드 조작: Tab / Shift+Tab = 다음·이전 BBox 선택, Shift+방향키 = 1px 미세 이동(Ctrl 도 누르면 10px), H = BBox 숨기기
        for key in ("<Tab>", "<Shift-Tab>", "<ISO_Left_Tab>"):
            r.bind(key, lambda e, k=key: None if self.is_typing(e) else self.select_next_box(+1 if k == "<Tab>" else -1))
        for name, (dx, dy) in {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}.items():
            r.bind(f"<Shift-{name}>", lambda e, d=(dx, dy): None if self.is_typing(e) else self.nudge(*d, big=False))
            r.bind(f"<Control-Shift-{name}>", lambda e, d=(dx, dy): None if self.is_typing(e) else self.nudge(*d, big=True))
        for key in ("h", "H"):
            r.bind(key, lambda e: None if self.is_typing(e) else self.toggle_boxes())

        r.bind("<F1>", lambda e: self.show_help())

        # Ctrl+G = 사진 번호 입력칸으로 커서 이동 (번호로 바로 이동)
        for key in ("<Control-g>", "<Control-G>"):
            r.bind(key, lambda e: self.focus_jump_entry())

    TOOLTIPS = {
        "이미지 열기": "사진 1장을 열어요",
        "폴더 열기": "폴더 안의 사진 전체를 열어요 (폴더를 창에 끌어다 놓아도 돼요)",
        "저장": "Ctrl+S — 지금의 BBox 와 검수 기록을 저장해요",
        "저장+다음": "W — 저장하고 바로 다음 사진으로 가요",
        "↶ 되돌리기": "Ctrl+Z — 방금 한 편집을 되돌려요",
        "↷ 다시": "Ctrl+Y — 되돌린 편집을 다시 적용해요",
        "삭제": "Delete — 선택한 BBox 를 지워요",
        "전체 삭제": "이 사진의 BBox 를 모두 지워요 (Ctrl+Z 로 되돌릴 수 있어요)",
        "⤢ 맞춤": "F — 이미지 전체가 보이게 맞춰요",
        "－": "축소 (마우스 휠 아래로)",
        "＋": "확대 (마우스 휠 위로)",
        "이동 모드": "켜면 왼쪽 버튼으로 끌어서 화면을 옮길 수 있어요 (끄면 다시 BBox 편집)",
    }

    def show_help(self):
        """[도구 ▸ 단축키 도움말] / F1"""
        show_shortcuts(self.root)

    @staticmethod
    def is_typing(event):
        """키를 누른 곳이 글자 입력칸(Entry·Combobox)인가?"""
        return isinstance(event.widget, (tk.Entry, ttk.Entry))


    # ====================================================================
    # 데이터 조사 / 폴더 열기
    # ====================================================================

    def show_inventory(self):
        """[데이터 조사] RAW 폴더의 개수·짝·빈 TXT·Class 분포를 표로 보여 준다."""
        rows, summary = scan_inventory(settings.RAW_DIR)
        if not rows:
            messagebox.showinfo("데이터 조사", f"조사할 데이터가 없습니다.\n\n{settings.RAW_DIR}\n\n"
                                "이 폴더 안에 이물검출_학습데이터1, 이물검출_학습데이터2 폴더(images / labels 포함)를 넣어 주세요.")
            return
        text = inventory_markdown(rows, summary)

        win = tk.Toplevel(self.root)
        win.title("데이터 조사 결과 (RAW 를 읽기만 한 결과)")
        win.geometry("820x600")
        win.configure(bg=theme.COLORS["bg"])
        box = tk.Text(win, font=theme.mono(10), wrap="none", bg=theme.COLORS["card"], fg=theme.COLORS["text"],
                      relief="flat", padx=12, pady=10, highlightthickness=1, highlightbackground=theme.COLORS["border"])
        box.insert("1.0", text)
        box.config(state="disabled")
        btns = ttk.Frame(win, padding=(10, 8))
        btns.pack(side="bottom", fill="x")

        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.set_status("조사 표를 복사했습니다. 옵시디언 노트에 붙여 넣으세요 (Ctrl+V).")

        ttk.Button(btns, text="표 복사 (마크다운)", command=copy, style="Primary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="닫기", command=win.destroy, style="Tool.TButton").pack(side="left")
        box.pack(fill="both", expand=True)

    def run_validation(self):
        """[무결성 검증(QA)] 900장 전체 데이터셋 무결성을 정밀 검사하여 결과 다이얼로그를 띄운다."""
        self.set_status("데이터셋 무결성 검사(Validation) 진행 중...")
        self.root.update_idletasks()
        report = validate_dataset(raw_dir=settings.RAW_DIR, work_dir=settings.WORK_DIR)
        
        out_csv = settings.PROJECT_DIR / "reports" / "validation_report.csv"
        write_report(report, out_csv)
        self.set_status(f"검증 완료: 총 {len(report)}건의 결과 (보고서: reports/validation_report.csv)")

        def jump_to_file(rel_path):
            found = find_raw_image(rel_path)
            if found is not None:
                self.move_to(found)
            else:
                messagebox.showinfo("안내", f"해당 이미지 파일을 찾을 수 없습니다: {rel_path}")

        show_validation_dialog(self.root, report, csv_path=out_csv, on_jump=jump_to_file)

    def open_work_folder(self):
        """[WORK 폴더 열기] 저장 결과를 파일 탐색기에서 확인한다."""
        settings.WORK_DIR.mkdir(parents=True, exist_ok=True)
        folder = settings.WORK_DIR
        try:
            if hasattr(os, "startfile"):                          # Windows
                os.startfile(folder)
                return
            if shutil.which("wslpath") and shutil.which("explorer.exe"):   # WSL → Windows 탐색기로 연다
                win_path = subprocess.run(["wslpath", "-w", str(folder)], capture_output=True, text=True,
                                          check=True).stdout.strip()
                subprocess.Popen(["explorer.exe", win_path])      # explorer.exe 는 성공해도 종료 코드 1 을 돌려주므로 결과는 보지 않는다
                return
            if shutil.which("xdg-open"):                          # 일반 Linux
                subprocess.Popen(["xdg-open", str(folder)])
                return
        except (OSError, subprocess.SubprocessError):
            pass
        messagebox.showinfo("WORK 폴더", str(folder))             # 열 수 없는 환경에서는 경로만 알려 준다

    # ====================================================================
    # 파일 열기 / 저장 / 다시 불러오기
    # ====================================================================

    def open_image(self):
        """[이미지 열기] 파일 선택 → 불러오기."""
        if not self.confirm_discard():
            return
        path = filedialog.askopenfilename(
            title="라벨링할 이미지 선택 (data/raw/.../images/...)",
            initialdir=str(settings.RAW_DIR if settings.RAW_DIR.is_dir() else settings.PROJECT_DIR),
            filetypes=[("JPG 이미지", "*.jpg *.jpeg *.JPG *.JPEG")])
        if path:
            self.load_image(path)

    def restore_session(self):
        """프로그램을 켠 직후, 마지막으로 보던 폴더와 사진을 그대로 연다. 이미 뭔가 열었거나 기록이 없으면 아무것도 안 한다."""
        if self.pil_image is not None:
            return False
        saved = load_session()
        if saved is None:
            return False
        folder, image = saved
        first = self.navigator.load_folder(folder)
        if first is None or image not in self.navigator.files:
            return False
        if not self.load_image(image):
            return False
        self.set_status(f"마지막 작업 위치에서 이어서 시작합니다: {image.name}  ({self.navigator.progress_text()})")
        return True

    def open_folder(self):
        """[폴더 열기] 폴더를 고르면 그 안의 사진 전체를 목록으로 열고 첫 사진을 보여 준다."""
        folder = filedialog.askdirectory(
            title="사진이 들어 있는 폴더 선택 (data/raw/... 또는 images 폴더)",
            initialdir=str(settings.RAW_DIR if settings.RAW_DIR.is_dir() else settings.PROJECT_DIR))
        if folder:
            self.open_folder_path(folder)

    def open_folder_path(self, folder):
        """폴더 안의 사진을 목록으로 쓰고 첫 사진을 연다.  ([폴더 열기] 와 끌어다 놓기가 함께 쓴다)"""
        if not self.confirm_discard():
            return
        first = self.navigator.load_folder(folder)
        if first is None:                                                  # 사진이 없으면 지금 화면·목록을 그대로 둔다
            messagebox.showinfo("사진이 없음", f"이 폴더에는 JPG 사진이 없습니다.\n\n{folder}")
            return
        if not self.load_image(first):
            return
        text = f"폴더를 열었습니다: {Path(folder).name} (총 {self.navigator.total}장)"
        if not is_inside(Path(folder), settings.RAW_DIR):
            text += "   ※ data/raw 밖의 폴더라 검수표에는 기록되지 않습니다"
        self.set_status(text)

    def on_drop(self, paths):
        """창에 폴더(또는 사진)를 끌어다 놓았을 때."""
        target = pick_target(paths)
        if target is None:
            messagebox.showinfo("열 수 없음", "폴더나 JPG 사진을 놓아 주세요.")
            return
        kind, path = target
        if kind == "folder":
            self.open_folder_path(path)
        elif self.confirm_discard():
            self.load_image(path)

    @staticmethod
    def decode_image(path):
        """사진 파일을 읽어 RGB 이미지로. (무거운 작업 — 화면 요소를 건드리지 않아서 다른 스레드에서도 안전하다)"""
        img = Image.open(path)
        img.load()
        return img.convert("RGB")

    def load_image(self, path):
        """이미지 1장을 읽어 화면에 올린다. (저장 여부 확인은 부르는 쪽에서 이미 끝낸 상태)"""
        try:
            img = self.decode_image(path)
        except Exception as e:
            messagebox.showerror("이미지를 열 수 없음", f"{path}\n\n{e}")
            return False
        self.apply_image(path, img)
        return True

    def apply_image(self, path, img, keep_pending=False):
        """읽은 사진을 화면에 올린다. keep_pending=True 면 방향키로 가는 중인 목적지(_nav_pending)를 지우지 않는다."""
        self._load_seq += 1                           # 읽는 중이던 다른 결과는 이제 낡은 것
        if not keep_pending:
            self._nav_pending = None                  # 다른 경로로 사진을 열면 방향키로 가던 중이던 목적지는 버린다
        self.image_path = Path(path)
        self.pil_image = img
        self.img_w, self.img_h = img.size
        self.navigator.set_current(self.image_path)   # 목록·번호 갱신
        self.load_boxes()
        self.show_image()                                    # 새 이미지는 항상 '화면 맞춤'으로 시작
        self.update_nav()
        save_session(self.navigator.folder, self.image_path)  # 다음에 켜면 여기서 이어서 (작은 파일 하나)

    # ---- 방향키로 넘길 때: 사진 읽기를 다른 스레드에서 ----
    def start_async_load(self, index):
        """navigator.files[index] 를 다른 스레드에서 읽기 시작한다. 읽는 동안 화면(번호·목록)은 계속 움직인다."""
        path = self.navigator.files[index]
        st = {"path": path, "seq": self._load_seq, "done": False, "img": None, "error": None}
        self._load_state = st

        def work():
            try:
                st["img"] = self.decode_image(path)
            except Exception as e:  # noqa: BLE001 — 깨진 사진은 화면 쪽에서 안내한다
                st["error"] = e
            st["done"] = True

        threading.Thread(target=work, daemon=True).start()
        if self._poll_job is None:
            self._poll_job = self.root.after(6, self.poll_load)

    def poll_load(self):
        """다른 스레드가 사진을 다 읽었는지 확인하고, 다 읽었으면 화면에 올린다. (화면은 이 함수에서만 건드린다)"""
        self._poll_job = None
        st = self._load_state
        if st is None:
            return
        if not st["done"]:
            self._poll_job = self.root.after(6, self.poll_load)
            return
        if self.drag is not None:                            # 마우스로 BBox 를 끄는 중에는 화면을 바꾸지 않고 잠깐 기다린다
            self._poll_job = self.root.after(30, self.poll_load)
            return
        self._load_state = None
        files = self.navigator.files
        pending = self._nav_pending
        target = files[pending] if pending is not None and 0 <= pending < len(files) else None
        if st["seq"] != self._load_seq:                      # 읽는 사이에 다른 경로로 사진이 열렸다 → 이 결과는 버린다
            return
        if target is None:                                   # 가려던 곳이 사라졌다(목록이 바뀜)
            self._nav_pending = None
            self.update_nav()
            return
        if st["error"] is not None:
            if target == st["path"]:                         # 가려던 사진 자체가 깨졌다 → 안내하고 지금 사진에 머문다
                self._nav_pending = None
                messagebox.showerror("이미지를 열 수 없음", f"{st['path']}\n\n{st['error']}")
                self.update_nav()
            else:                                            # 지나가는 사진이 깨졌으면 건너뛰고 최신 목적지를 읽는다
                self.start_async_load(pending)
            return
        if self._edit_serial != self._nav_serial:            # 읽는 동안 편집했다 → 편집 중인 내용을 지키려고 이동을 취소한다
            self._nav_pending = None
            self.update_nav()
            self.set_status("편집 중인 내용이 있어 사진 이동을 취소했습니다. 저장하거나 되돌린 뒤 다시 넘겨 주세요.")
            return
        final = target == st["path"]
        self.apply_image(st["path"], st["img"], keep_pending=not final)
        if not final:                                        # 지나가는 사진: 화면에는 올렸지만 가려는 곳은 더 앞이다 → 표시를 목적지로 되돌리고 계속 읽는다
            self.show_nav_number(pending + 1)
            self.btn_prev.config(state="normal" if pending > 0 else "disabled")
            self.btn_next.config(state="normal" if pending < self.navigator.total - 1 else "disabled")
            self.strip.set_current(pending)
            self.start_async_load(pending)

    def wait_for_nav(self, timeout=10.0):
        """방향키 이동이 끝날 때까지 기다린다 (시험·자동화용). 끝났으면 True."""
        end = time.monotonic() + timeout
        while self._nav_pending is not None or self._nav_job is not None or self._load_state is not None:
            if time.monotonic() > end:
                return False
            self.root.update()
            time.sleep(0.002)
        return True

    # ---- 이전 / 다음 ----
    def go_prev(self):
        self.step(-1)

    def go_next(self):
        self.step(+1)

    def step(self, delta):
        """이전(-1) / 다음(+1).  방향키를 누르고 있으면 입력이 초당 수십 번 들어와 사진을 그때마다 읽으면 쌓여서 멈춰 보인다.
        그래서 번호·목록 표시만 바로 바꾸고, 사진은 입력이 잠잠해지는 순간(after_idle)에 '가려는 곳' 한 장만 읽는다."""
        nav = self.navigator
        base = self._nav_pending if self._nav_pending is not None else nav.index
        target = base + delta
        if not 0 <= target < nav.total:
            return
        if self._nav_pending is None:
            if not self.confirm_discard():                              # 저장 안 한 변경이 있으면 처음 한 번만 물어봄
                return
            self._nav_serial = self._edit_serial                        # 여기서부터 새로 편집하면 이동을 취소해 지킨다
        self._nav_pending = target
        self.show_nav_number(target + 1)                                # 가벼운 표시만 먼저 갱신
        self.btn_prev.config(state="normal" if target > 0 else "disabled")
        self.btn_next.config(state="normal" if target < nav.total - 1 else "disabled")
        self.strip.set_current(target)                                  # 하단 미리보기 줄의 강조도 바로 옮긴다 (가벼움)
        if self._nav_job is None:
            self._nav_job = self.root.after_idle(self.flush_step)

    def flush_step(self):
        """쌓인 이동 중 마지막 목적지 사진을 읽기 시작한다. (이미 읽는 중이면 그것이 끝난 뒤 poll_load 가 최신 목적지를 이어서 읽는다)"""
        self._nav_job = None
        target = self._nav_pending
        if target is None or not 0 <= target < self.navigator.total:
            self._nav_pending = None
            return
        if self._load_state is None:
            self.start_async_load(target)

    def move_to(self, path):
        if path is None or not self.confirm_discard():   # 저장 안 한 변경이 있으면 먼저 물어봄
            return
        self.load_image(path)

    def show_nav_number(self, number):
        """번호 입력칸과 '/ 총 개수' 를 맞춘다. (number = 1부터, 사진이 없으면 0)"""
        self.entry_index.delete(0, "end")
        self.entry_index.insert(0, str(number))
        self.total_label.config(text=f"/ {self.navigator.total}")

    def nav_text(self):
        """화면에 보이는 위치 글자 (예: '21 / 300')."""
        return f"{self.entry_index.get()} {self.total_label.cget('text')}"

    def focus_jump_entry(self):
        """Ctrl+G : 사진 번호 입력칸에 커서를 두고 전체를 선택한다."""
        self.entry_index.focus_set()
        self.entry_index.select_range(0, "end")

    def jump_to_entered_index(self):
        """입력한 사진 번호(1부터)로 바로 이동한다.  예: 300 → 300번째 사진."""
        nav = self.navigator
        current = nav.index + 1 if nav.index >= 0 else 0
        if nav.total == 0:
            messagebox.showinfo("이동", "열려 있는 사진 목록이 없습니다. 먼저 [폴더 열기] 또는 [이미지 열기]로 사진을 불러오세요.")
            return
        text = self.entry_index.get().strip()
        if not text:
            self.show_nav_number(current)
            return
        if not text.isdigit() or not 1 <= int(text) <= nav.total:
            messagebox.showwarning("사진 번호", f"1부터 {nav.total} 사이의 숫자를 입력해 주세요.\n(입력값: '{text}')")
            self.show_nav_number(current)
            return
        if int(text) != current:
            self.move_to(nav.jump_to_index(int(text) - 1))
        self.show_nav_number(nav.index + 1)                 # 저장 확인에서 취소했으면 원래 번호로 되돌린다
        self.canvas.focus_set()                             # 이동 후 방향키·단축키가 바로 동작하도록

    def update_nav(self):
        """진행률 글자와 [이전]/[다음] 버튼 활성 상태를 맞춘다."""
        nav = self.navigator
        self.show_nav_number(nav.index + 1 if nav.index >= 0 else 0)
        self.btn_prev.config(state="normal" if nav.has_prev() else "disabled")
        self.btn_next.config(state="normal" if nav.has_next() else "disabled")
        self.refresh_file_list()

    def refresh_file_list(self):
        """하단 사진 목록을 채우고 현재 사진을 표시한다."""
        nav = self.navigator
        if not nav.filtered and self.filter_var.get() != self.FILTER_ALL:
            self.filter_var.set(self.FILTER_ALL)                 # 필터가 풀렸으면(새 폴더·숨겨진 사진 열기) 표시도 맞춘다
        if self._listed_files != nav.files:
            self._listed_files = list(nav.files)
            self.strip.set_files(nav.files, total_all=len(nav.all_files))
        self.strip.set_current(nav.index)
        self.update_summary()

    def update_summary(self):
        """사진 목록 제목줄에 작업 진행 요약 (예: 작업 3/11 (27%) · 검수 완료 1 · 수정 완료 1 · 수정 필요 1)."""
        files = self.navigator.all_files
        if not files:
            self.strip.summary.config(text="")
            return
        status_map = self.status_map()
        key = (self._status_cache[0], len(files), files[0], files[-1])
        if self._summary_key != key:                              # 검수표나 목록이 바뀐 때만 다시 센다
            counts = {}
            for p in files:
                st = status_of(p, status_map)
                if st:
                    counts[st] = counts.get(st, 0) + 1
            worked = sum(counts.values())
            parts = [f"작업 {worked}/{len(files)} ({round(worked * 100 / len(files))}%)"]
            for name in ("검수 완료", "수정 완료", "수정 필요", "제외", "검수 전"):
                if counts.get(name):
                    parts.append(f"{name} {counts[name]}")
            self._summary_key, self._summary_text = key, "  ·  ".join(parts)
        self.strip.summary.config(text=self._summary_text)

    def on_thumb_selected(self, index):
        """하단 사진 목록에서 사진을 눌렀을 때. (저장 확인에서 취소하면 그대로 남는다)"""
        files = self.navigator.files
        if 0 <= index < len(files) and index != self.navigator.index:
            self.move_to(files[index])
        self.strip.set_current(self.navigator.index)

    def status_map(self):
        """검수표의 {사진: 상태}. 파일이 바뀌었을 때만 다시 읽는다."""
        try:
            stamp = Path(settings.MANIFEST_PATH).stat().st_mtime_ns
        except OSError:
            stamp = None
        if self._status_cache[0] != stamp:
            try:
                data = read_status_map()
            except ManifestError:
                data = {}
            self._status_cache = (stamp, data)
        return self._status_cache[1]

    # ── 보기 필터 ─────────────────────────────────────────────────
    FILTER_ALL = "전체"
    FILTER_NONE = "미작업 (기록 없음)"
    FILTER_CHOICES = [FILTER_ALL, FILTER_NONE, "검수 전", "수정 완료", "검수 완료", "수정 필요", "제외"]

    def make_filter(self, name):
        """필터 이름 → 사진 경로를 받아 True/False 를 돌려주는 함수 (전체면 None). 검수표는 한 번만 읽는다."""
        if name == self.FILTER_ALL:
            return None
        status_map = self.status_map()
        if name == self.FILTER_NONE:
            return lambda p: status_of(p, status_map) == ""
        return lambda p: status_of(p, status_map) == name

    def on_filter_changed(self):
        """보기 필터를 바꿨을 때: 해당하는 사진만 목록·이동에 쓴다. 현재 사진이 해당하지 않으면 첫 사진으로 간다."""
        nav = self.navigator
        name = self.filter_var.get()
        if self.pil_image is None or not nav.all_files:
            self.filter_var.set(self.FILTER_ALL)
            if name != self.FILTER_ALL:
                self.set_status("먼저 폴더나 사진을 열어 주세요. 열린 사진이 있어야 걸러 볼 수 있습니다.")
            return
        count = nav.set_filter(self.make_filter(name))
        if count == 0:
            nav.set_filter(None)
            self.filter_var.set(self.FILTER_ALL)
            messagebox.showinfo("보기", f"'{name}' 에 해당하는 사진이 없습니다.")
            self.update_nav()                                    # 번호·총 개수·이전/다음 표시도 함께 되돌린다
            return
        if nav.index < 0:                                        # 지금 보던 사진이 걸러졌다 → 첫 사진으로
            if not self.confirm_discard():
                nav.set_filter(None)
                self.filter_var.set(self.FILTER_ALL)
                self.update_nav()
                return
            self.load_image(nav.files[0])
        else:
            self.update_nav()
        self.set_status(f"보기: {name} — {nav.total}장 (전체 {len(nav.all_files)}장)" if nav.filtered
                        else f"전체 보기 — {nav.total}장")

    THUMB_STATUS_COLORS = {"검수 전": "#555555", "수정 완료": "#e65100", "검수 완료": "#2e7d32",
                           "수정 필요": "#c62828", "제외": "#757575"}

    def thumb_mark(self, path):
        """사진 목록의 사진 아래 글자: 저장했으면 ✓, 검수표 상태가 있으면 상태 (색으로 구분)."""
        saved = work_label_path(path).exists()
        status = status_of(path, self.status_map())
        if not saved and not status:
            return "", "#555555"
        text = ("✓ " if saved else "") + status
        return text.strip(), self.THUMB_STATUS_COLORS.get(status, "#2e7d32")

    def load_boxes(self):
        """TXT 를 읽어 self.boxes 에 채운다.

        우선순위:  ① WORK 에 이미 저장한 TXT  →  ② RAW(원본) TXT  →  ③ 없으면 빈 목록
        ① 이 있으면 '내가 지난번에 고친 결과'를 이어서 작업한다.
        """
        self.boxes, self.selected, self.dirty = [], None, False
        self._clean = []
        self.unreadable = 0
        self.history.clear()                                 # 다른 이미지(또는 다시 불러오기)면 Undo 기록은 버린다
        raw_txt = find_raw_label(self.image_path)
        self.raw_boxes = read_yolo_file(raw_txt, self.img_w, self.img_h)[0] if raw_txt else []   # Diff 비교용 원본
        dataset, split = locate_in_raw(self.image_path)
        where = f"{dataset} / {split}" if dataset else "RAW 밖의 파일"
        self.info.config(text=self.image_path.name)
        self.info_meta.config(text=f"{where}   ·   {self.img_w} × {self.img_h} px")
        self.load_form()

        work = work_label_path(self.image_path)
        source = work if work.is_file() else find_raw_label(self.image_path)
        if source is None:
            self.set_status("TXT 가 없어 BBox 없이 시작합니다. (정상 이미지거나 라벨이 빠진 것일 수 있어요 → 이미지를 직접 확인)")
            return
        self.boxes, bad = read_yolo_file(source, self.img_w, self.img_h)
        self.unreadable = bad
        self._clean = [dict(b) for b in self.boxes]
        kind = "WORK(내가 저장한 것)" if source == work else "RAW(원본)"
        msg = f"{kind} TXT 에서 BBox {len(self.boxes)}개 로드: {source.name}"
        if not self.boxes and not bad:
            msg += "  ← 빈 TXT: 이물이 정말 없는지 이미지를 보고 확인하세요"
        if bad:
            msg += f"  ⚠ 읽지 못한 줄 {bad}개 (저장하면 WORK 파일에서는 빠집니다)"
        odd = sum(1 for b in self.boxes if self.problems_of(b))
        if odd:
            msg += f"  ⚠ 확인이 필요한 BBox {odd}개 (빨간 점선: 이미지 밖·Class 범위 밖 등)"
        self.set_status(msg)

    def save(self):
        """[저장] WORK 폴더에 YOLO TXT 로 저장.  RAW 는 절대 건드리지 않는다."""
        if self.pil_image is None:
            return False
        target = work_label_path(self.image_path)
        if self.unreadable and self._unreadable_ok != self.image_path:
            if not messagebox.askyesno("읽지 못한 줄이 있습니다",
                                       f"원본 라벨에 형식이 맞지 않아 읽지 못한 줄이 {self.unreadable}개 있습니다.\n\n"
                                       "저장하면 그 줄은 WORK 파일에 들어가지 않습니다. (원본은 그대로 남습니다)\n"
                                       "그래도 저장할까요?"):
                return False
            self._unreadable_ok = self.image_path
        # ★ 안전장치: 저장 경로가 RAW 안이면 저장을 거부한다. (RAW 원본을 수정하지 않는다)
        if is_inside(target, settings.RAW_DIR):
            messagebox.showerror("저장 거부", f"RAW 폴더에는 저장할 수 없습니다.\n\n{target}")
            return False
        try:
            write_yolo_file(target, self.boxes, self.img_w, self.img_h)
        except OSError as e:
            messagebox.showerror("저장 실패", f"저장하지 못했습니다.\n\n{e}")
            return False
        # TXT 저장이 끝난 뒤 검수표(CSV)에 이 사진의 줄을 기록한다. 입력칸 값(사람 칸)도 함께 넘긴다.
        # 실패해도 TXT 는 이미 저장되어 있다. 다만 입력칸 내용은 아직 기록되지 않았으므로 '저장 안 함' 상태로 둔다.
        try:
            note = record_save(self.image_path, find_raw_label(self.image_path), target, len(self.boxes),
                               human=self.form.get_values())
        except ManifestError as e:
            self.dirty = True
            self.update_title()
            messagebox.showwarning("검수표 기록 실패", "TXT 는 저장되었습니다.\n검수표(CSV)에는 기록하지 못했습니다.\n"
                                   f"입력칸 내용은 아직 기록되지 않았습니다.\n\n{e}")
            self.set_status(f"TXT 저장 완료 → {target}   |   검수표 기록 실패 (입력칸 내용 미기록)")
            return False
        self.dirty = False
        self.unreadable = 0
        self._clean = [dict(b) for b in self.boxes]
        self.update_title()
        self.update_warning()
        self.load_form()                     # 프로그램이 정한 상태(예: 수정 완료)를 입력칸에 다시 보여 준다
        self.strip.refresh_marks()           # 사진 목록에 ✓·상태 표시
        self.update_summary()                # 작업 진행 요약
        self.set_status(f"저장 완료 → {target}   |   {note}")
        return True

    def load_form(self):
        """검수표에 적혀 있던 상태·사람 칸을 입력칸에 보여 준다. (기록이 없으면 빈칸)"""
        try:
            values = read_human(self.image_path)
        except ManifestError as e:
            self.form.clear()
            try:
                stamp = Path(settings.MANIFEST_PATH).stat().st_mtime_ns
            except OSError:
                stamp = None
            if self._manifest_warned != stamp:                        # 같은 상태의 파일에 대해서는 경고창을 한 번만 (사진을 넘길 때마다 뜨면 곤란)
                self._manifest_warned = stamp
                messagebox.showwarning("검수표 읽기 실패", f"검수표(CSV)를 읽지 못해 입력칸을 비워 둡니다.\n\n{e}")
            self.manifest_ok = False                                  # 경고창 대신 이미지 위 경고 줄에 계속 표시한다
            return
        self._manifest_warned = "ok"
        self.manifest_ok = True
        self.form.set_values(values)

    def on_ime_mode(self, korean):
        """한/영 상태가 바뀌었을 때 상태줄에 알린다. (프로그램을 켤 때 처음 한 번은 알리지 않는다)"""
        if not getattr(self, "_ime_ready", False):
            self._ime_ready = True
            return
        self.set_status("한글 입력 — 검수 기록 칸에 한글로 쓸 수 있습니다. 영어로 바꾸려면 한/영 키를 다시 누르세요."
                        if korean else "영어 입력 — 한/영 키를 누르면 한글로 바뀝니다.")

    def on_form_changed(self):
        """입력칸을 고쳤을 때: 저장 안 한 변경으로 표시한다. (사진을 열기 전에는 저장할 곳이 없으므로 무시)"""
        if self.pil_image is None:
            return
        self._edit_serial += 1
        self.dirty = True
        self.update_title()

    def reload(self):
        """[다시 불러오기] 저장한 TXT 를 다시 읽어 BBox 가 같은 위치에 복원되는지 확인한다.

        '성공 기준' : 저장 → 다시 불러오기 → 같은 위치에 BBox 가 나타난다.
        (확대·이동 상태는 그대로 둔다 → 확대한 곳에서 바로 비교할 수 있다)
        """
        if self.pil_image is None:
            return
        if not self.confirm_discard():
            return
        self.load_boxes()
        self.draw_boxes()
        self.refresh_box_list()
        self.update_title()

    # ── 한 키 검수 ─────────────────────────────────────────────────
    def mark_ok_and_next(self):
        """Enter — 이 사진은 끝: 저장하고 다음 사진으로 넘어간다.
        원본과 같으면 상태를 '검수 완료', BBox 를 고쳤으면 '수정 완료'로 기록한다. (고친 사진이라는 정보가 검수표에서 사라지지 않도록)"""
        if self.pil_image is None or self.drag:
            return
        values = self.form.get_values()
        d = diff_boxes(self.raw_boxes, self.boxes)
        edited = bool(d["added"] or d["modified"] or d["deleted"])
        values["상태"] = STATUS_EDITED if edited else STATUS_DONE
        self.form.set_values(values)
        self.save_and_next()

    def mark_review(self):
        """R — 수정 필요: 상태를 '수정 필요'로 바꾸고 '발견된 문제'에 'REVIEW: ' 를 채운 뒤 이유를 쓰도록 커서를 옮긴다.
        이유를 쓰고 Enter 를 누르면 저장하고 다음 사진으로 간다."""
        if self.pil_image is None or self.drag:
            return
        values = self.form.get_values()
        values["상태"] = STATUS_REVIEW
        if not values["발견된 문제"]:
            values["발견된 문제"] = "REVIEW: "
        self.form.set_values(values)
        self.on_form_changed()                                   # 저장 안 한 변경으로 표시
        self.form.focus_field("발견된 문제")
        self.set_status("수정 필요로 표시했습니다 — 이유를 쓰고 Enter 를 누르면 저장하고 다음 사진으로 갑니다.")

    def on_form_submit(self):
        """검수 기록 글자 칸에서 Enter: 저장하고 다음 사진으로. (이미지 화면으로 커서를 돌려 단축키가 바로 동작하게)"""
        self.canvas.focus_set()
        self.save_and_next()

    def go_next_unworked(self):
        """N — 아직 검수표에 기록이 없는 다음 사진으로 건너뛴다. (끝까지 없으면 처음부터 다시 찾는다)"""
        nav = self.navigator
        if not nav.files:
            self.set_status("먼저 폴더나 사진을 열어 주세요.")
            return
        status_map = self.status_map()
        start = nav.index
        for i in list(range(start + 1, nav.total)) + list(range(0, max(start, 0))):
            if status_of(nav.files[i], status_map) == "":
                self.move_to(nav.files[i])
                return
        self.set_status("아직 작업하지 않은 사진이 없습니다. 모두 검수표에 기록되어 있어요.")

    def save_and_next(self):
        """[저장 후 다음] / W : 저장하고 바로 다음 사진으로 넘어간다. (저장에 실패하면 넘어가지 않는다)"""
        if self.pil_image is None or self.drag:
            return
        if not self.save():
            return
        if not self.navigator.has_next():
            self.set_status(self.status.cget("text") + "   |   마지막 사진입니다.")
            return
        self.go_next()

    def confirm_discard(self):
        """저장 안 한 변경이 있으면 물어본다. True = 계속 진행해도 됨."""
        if not self.dirty:
            return True
        ans = messagebox.askyesnocancel("저장하지 않은 변경", "저장하지 않은 변경이 있습니다.\n저장할까요?")
        if ans is None:
            return False                     # 취소
        return self.save() if ans else True  # 예 → 저장 / 아니오 → 변경 버림

    def shutdown(self):
        """예약해 둔 작업(화면 다시 그리기·이동·복원 등)을 모두 취소한다. 창을 닫기 직전에 부른다.
        (취소하지 않으면 닫힌 창을 찾다가 'invalid command name' 오류가 날 수 있다)"""
        self._load_state = None                                  # 읽는 중이던 사진은 버린다 (스레드는 알아서 끝난다)
        for name in ("_resize_job", "_render_job", "_nav_job", "_restore_job", "_poll_job"):
            job = getattr(self, name, None)
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, name, None)
        self.strip.stop()

    def on_close(self):
        if self.confirm_discard():
            self.shutdown()
            self.root.destroy()

    # ====================================================================
    # 화면 그리기
    #    ★ 성능 팁 1: '이미지'와 'BBox' 를 따로 그린다.
    #      이미지는 줄이는 계산이 무거우므로 열 때 / 창 크기 / 확대·이동이 바뀔 때만 다시 만들고,
    #      BBox 는 가벼우니 바뀔 때마다 다시 그린다.
    #    ★ 성능 팁 2: 확대했을 때는 '화면에 보이는 부분만' 잘라서 키운다.
    #      4K 사진을 2000 % 로 통째로 키우면 메모리가 터진다.
    # ====================================================================

    def canvas_size(self):
        c = self.canvas
        return max(c.winfo_width(), 50), max(c.winfo_height(), 50)

    def show_image(self):
        """이미지를 현재 캔버스 크기에 맞춰(Fit to Window) 다시 그린다."""
        c = self.canvas
        if self.pil_image is None:
            c.delete("img")
            c.delete("box")
            c.create_text(c.winfo_width() / 2, c.winfo_height() / 2, tags="img", fill=theme.COLORS["faint"],
                          font=theme.font(13), justify="center",
                          text="사진을 열어 주세요\n\n위의 [폴더 열기] 를 누르거나, 폴더를 이 창에 끌어다 놓으세요\n(데이터는 data/raw 폴더에 넣어 두세요)")
            self.refresh_box_list()
            return
        cw, ch = self.canvas_size()
        self.vp.fit(self.img_w, self.img_h, cw, ch, upscale=True)   # 가로·세로 중 더 빡빡한 쪽에 맞춤
        self.auto_fit = True
        self.render()
        self.refresh_box_list()
        self.update_title()

    def render(self):
        """현재 Viewport(배율·위치) 그대로 이미지 + BBox 를 다시 그린다."""
        self._render_job = None
        self.zoom_label.config(text=f"{self.vp.zoom_percent}%" if self.pil_image is not None else "")
        c = self.canvas
        c.delete("img")
        if self.pil_image is None:
            return
        cw, ch = self.canvas_size()
        # 캔버스 네 귀퉁이가 원본 이미지의 어디에 해당하는지 → 그 부분만 잘라 낸다
        ix0, iy0 = self.vp.canvas_to_image(0, 0)
        ix1, iy1 = self.vp.canvas_to_image(cw, ch)
        x0, y0 = max(0, math.floor(ix0)), max(0, math.floor(iy0))
        x1, y1 = min(self.img_w, math.ceil(ix1)), min(self.img_h, math.ceil(iy1))
        if x1 > x0 and y1 > y0:
            disp_w = max(1, round((x1 - x0) * self.vp.scale))
            disp_h = max(1, round((y1 - y0) * self.vp.scale))
            # 크게 확대하면 픽셀 경계가 보이도록 NEAREST (경계를 정확히 맞추기 좋다)
            resample = Image.NEAREST if self.vp.scale >= 2 else Image.BILINEAR
            part = self.pil_image.crop((x0, y0, x1, y1))
            shrink = next((k for k in (8, 4, 2) if self.vp.scale * k <= 1), 1) if resample == Image.BILINEAR else 1
            if shrink > 1:
                part = part.reduce(shrink)                   # 크게 줄여 보일 때는 먼저 정수 배로 줄여 두면 훨씬 빠르다 (4K 사진 39ms → 18ms)
            part = part.resize((disp_w, disp_h), resample)
            part = self.enhance(part)                        # 밝기·대비·흑백 (화면에 보이는 부분만 — 가벼움)
            self.photo = ImageTk.PhotoImage(part)            # self.photo 에 저장해 두지 않으면 화면에서 사라진다!
            sx, sy = self.vp.image_to_canvas(x0, y0)
            c.create_image(round(sx), round(sy), anchor="nw", image=self.photo, tags="img")
            c.tag_lower("img")                               # 이미지는 맨 아래, BBox 가 그 위에 오도록
        else:
            self.photo = None                                # 이미지가 화면 밖으로 완전히 나감
        self.draw_boxes()

    def update_warning(self):
        """이미지 위쪽의 경고 줄: 읽지 못한 줄 · 확인이 필요한 BBox 개수. 문제가 없으면 비운다."""
        parts = []
        if self.unreadable:
            parts.append(f"읽지 못한 줄 {self.unreadable}개 (저장하면 WORK 파일에서 빠집니다)")
        odd = sum(1 for b in self.boxes if self.problems_of(b))
        if odd:
            parts.append(f"확인이 필요한 BBox {odd}개")
        if not self.manifest_ok:
            parts.append("검수표(CSV)를 읽지 못해 검수 기록 칸이 비어 있습니다 (파일을 고친 뒤 다시 열어 주세요)")
        text = "⚠ " + "  ·  ".join(parts) if parts else ""
        if self.warn_label.cget("text") != text:
            self.warn_label.config(text=text)

    def problems_of(self, box):
        """이 BBox 에서 이상한 점 (이미지 밖·Class 범위 밖·너무 작음 등). 정상이면 빈 목록."""
        return box_problems(box, self.img_w, self.img_h, len(settings.CLASSES), settings.UNUSED_CLASSES)

    DIFF_COLORS = {"added": "#2e7d32", "modified": "#ef6c00", "deleted": "#c62828"}     # 추가 초록 · 수정 주황 · 삭제 빨강
    DIFF_NAMES = {"added": "추가", "modified": "수정", "deleted": "삭제"}

    def draw_boxes(self):
        """BBox 만 다시 그린다 (가벼움). 원본 픽셀 좌표 → 화면 좌표 변환이 핵심.
        [RAW 와 비교(Diff)] 를 켜면 추가(초록)·수정(주황)·삭제(빨강)를 색으로 구분하고, 원본 위치는 점선으로 보여 준다."""
        c = self.canvas
        c.delete("box")
        if not self.show_boxes_var.get():                        # 숨김 상태: BBox 는 그리지 않는다 (목록·좌표줄은 그대로)
            self.update_bbox_info()
            self.update_warning()
            return
        state = {}                                               # state: 지금 BBox 번호 → 'added' / 'modified'
        if self.diff_var.get():
            d = diff_boxes(self.raw_boxes, self.boxes)
            state = {ci: "added" for ci in d["added"]}
            for ri, ci in d["modified"]:
                state[ci] = "modified"
                self.draw_ghost(self.raw_boxes[ri], "#9e9e9e", "원본")      # 수정 전 위치(회색 점선)
            for ri in d["deleted"]:
                self.draw_ghost(self.raw_boxes[ri], self.DIFF_COLORS["deleted"], "삭제됨")
            self.diff_label.config(text=diff_summary(d) + ("" if self.raw_boxes or not self.boxes else "  (원본 라벨이 없는 사진)"))
        for i, b in enumerate(self.boxes):
            x1, y1, x2, y2 = self.vp.box_to_canvas(b)
            color = settings.class_color(b["cls"])
            is_sel = (i == self.selected)
            mark = state.get(i)                                  # 'added' / 'modified' / None(그대로)
            problem = bool(self.problems_of(b))                  # 이상한 BBox 는 빨간 점선 + '⚠' 표시
            outline = "#ffeb3b" if is_sel else (theme.COLORS["danger"] if problem else
                                                (self.DIFF_COLORS[mark] if mark else color))
            c.create_rectangle(x1, y1, x2, y2, outline=outline, width=(4 if is_sel else 2),
                               dash=(6, 4) if problem else (), tags="box")
            label = f"{'⚠ ' if problem else ''}{b['cls']} {settings.class_name(b['cls'], with_note=False)}"
            if mark:
                label += f"  [{self.DIFF_NAMES[mark]}]"
            tag = c.create_text(x1 + 3, y1 - 2 if y1 > 16 else y1 + 12, anchor=("sw" if y1 > 16 else "nw"),
                                text=label, fill="white", font=theme.font(9, True), tags="box")
            bg = c.create_rectangle(c.bbox(tag), fill=(self.DIFF_COLORS[mark] if mark else color),
                                    outline=(self.DIFF_COLORS[mark] if mark else color), tags="box")
            c.tag_raise(tag, bg)                             # 글자가 배경 사각형 위에 오도록
        if self.selected is not None and self.selected < len(self.boxes):
            for hx, hy in handle_points(self.boxes[self.selected]).values():     # 선택된 BBox 의 크기 조절 핸들 8개
                sx, sy = self.vp.image_to_canvas(hx, hy)
                c.create_rectangle(sx - 4, sy - 4, sx + 4, sy + 4, fill="white", outline="#222222", width=1,
                                   tags=("box", "handle"))
        self.update_bbox_info()
        self.update_warning()

    def draw_ghost(self, b, color, text):
        """Diff 에서 원본 BBox 를 점선으로 그린다 (선택·이동 대상은 아니다)."""
        x1, y1, x2, y2 = self.vp.box_to_canvas(b)
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2, dash=(6, 4), tags="box")
        self.canvas.create_text(x1 + 3, y2 - 2, anchor="sw", text=f"{text} · {b['cls']}", fill=color,
                                font=theme.font(9, True), tags="box")

    ENHANCE_STEPS = (1.0, 1.3, 1.6, 0.7)     # 누를 때마다 순서대로 바뀌고 다시 1.0 으로 돌아온다

    def enhance(self, img):
        """화면 보정을 적용한 사본. (원본 pil_image 는 건드리지 않는다)"""
        if self.bright_idx:
            img = ImageEnhance.Brightness(img).enhance(self.ENHANCE_STEPS[self.bright_idx])
        if self.contrast_idx:
            img = ImageEnhance.Contrast(img).enhance(self.ENHANCE_STEPS[self.contrast_idx])
        if self.gray:
            img = img.convert("L").convert("RGB")
        return img

    def refresh_enhance(self, what):
        self.btn_bright.config(text=f"밝기 ×{self.ENHANCE_STEPS[self.bright_idx]:.1f}")
        self.btn_contrast.config(text=f"대비 ×{self.ENHANCE_STEPS[self.contrast_idx]:.1f}")
        self.gray_var.set(self.gray)
        self.render()
        self.set_status(f"{what} — 화면에만 적용됩니다. 원본 사진과 저장되는 라벨은 바뀌지 않습니다.")

    def cycle_brightness(self):
        self.bright_idx = (self.bright_idx + 1) % len(self.ENHANCE_STEPS)
        self.refresh_enhance("밝기")

    def cycle_contrast(self):
        self.contrast_idx = (self.contrast_idx + 1) % len(self.ENHANCE_STEPS)
        self.refresh_enhance("대비")

    def on_gray_clicked(self):
        """[흑백] 체크 버튼을 눌렀을 때 (체크 상태가 곧 켜짐/꺼짐)."""
        self.gray = self.gray_var.get()
        self.refresh_enhance("흑백 " + ("켜짐" if self.gray else "꺼짐"))

    def toggle_gray(self):
        self.gray = not self.gray
        self.refresh_enhance("흑백 " + ("켜짐" if self.gray else "꺼짐"))

    def on_pan_toggled(self):
        """[이동] 켜기/끄기."""
        self.set_cursor("fleur" if self.pan_var.get() else "crosshair")
        self.set_status("이동 모드 — 왼쪽 버튼으로 끌어 화면을 옮깁니다. (끄면 다시 BBox 를 그리고 고칩니다)"
                        if self.pan_var.get() else "이동 모드를 껐습니다.")

    def update_cross(self, x, y):
        """[십자선] 이 켜져 있으면 마우스 위치에 가로·세로 점선을 그린다 (BBox 경계를 정밀하게 맞출 때)."""
        self.canvas.delete("cross")
        if not self.cross_var.get() or self.pil_image is None:
            return
        cw, ch = self.canvas_size()
        self.canvas.create_line(0, y, cw, y, fill="#00e5ff", dash=(3, 3), tags="cross")
        self.canvas.create_line(x, 0, x, ch, fill="#00e5ff", dash=(3, 3), tags="cross")

    def on_cross_toggled(self):
        if not self.cross_var.get():
            self.canvas.delete("cross")
        else:
            self.set_status("십자선 켜짐 — 마우스를 따라다니는 점선으로 BBox 경계를 정밀하게 맞출 수 있습니다.")

    def on_diff_toggled(self):
        """[RAW 와 비교(Diff)] 켜기/끄기."""
        if not self.diff_var.get():
            self.diff_label.config(text="")
        self.draw_boxes()
        if self.diff_var.get():
            self.set_status("Diff 보기 — 초록 = 추가 · 주황 = 수정(회색 점선이 원래 위치) · 빨강 점선 = 삭제된 원본 BBox")

    def update_bbox_info(self):
        """선택한 BBox 의 좌표(원본 픽셀)와 YOLO 비율값을 상태줄 위에 보여 준다."""
        if self.selected is None or self.selected >= len(self.boxes):
            self.bbox_info.config(text="선택된 BBox 없음 — BBox 를 클릭하면 좌표가 여기에 표시됩니다")
            return
        b = self.boxes[self.selected]
        xc, yc, w, h = pixel_to_yolo(b["x1"], b["y1"], b["x2"], b["y2"], self.img_w, self.img_h)
        self.bbox_info.config(
            text=f"BBox {self.selected + 1}번 · Class {b['cls']}   "
                 f"x1,y1=({b['x1']:.0f}, {b['y1']:.0f})  x2,y2=({b['x2']:.0f}, {b['y2']:.0f})  "
                 f"W×H={b['x2'] - b['x1']:.0f}×{b['y2'] - b['y1']:.0f}px   "
                 f"YOLO xc={xc:.4f} yc={yc:.4f} w={w:.4f} h={h:.4f}"
                 + ("   ⚠ " + " · ".join(self.problems_of(b)) if self.problems_of(b) else ""))

    def refresh_box_list(self):
        """오른쪽 '라벨 목록' 표를 현재 self.boxes 와 맞춘다.  상태 = 원본 그대로이면 '원본', 고치거나 새로 그렸으면 '변경'."""
        self._box_guard = True
        try:
            self.box_list.delete(*self.box_list.get_children())
            same = set(diff_boxes(self.raw_boxes, self.boxes)["unchanged"])
            for i, b in enumerate(self.boxes):
                w, h = b["x2"] - b["x1"], b["y2"] - b["y1"]
                changed = i not in same
                problem = bool(self.problems_of(b))
                tags = ("problem",) if problem else (("changed",) if changed else ())
                self.box_list.insert("", "end", iid=str(i), tags=tags, values=(
                    i + 1, f"{b['cls']} {settings.class_name(b['cls'], with_note=False)}",
                    f"[{b['x1']:.0f},{b['y1']:.0f},{w:.0f},{h:.0f}]",
                    "⚠ 확인" if problem else ("변경" if changed else "원본")))
            if self.selected is not None and self.selected < len(self.boxes):
                self.box_list.selection_set(str(self.selected))
                self.box_list.see(str(self.selected))
            self.box_title.config(text=f"라벨 목록 ({len(self.boxes)}개)")
        finally:
            self._box_guard = False

    def update_title(self):
        self.dirty_label.config(text="● 저장 안 됨 (Ctrl+S)" if self.dirty and self.pil_image is not None else "")
        name = self.image_path.name if self.image_path else ""
        self.root.title(f"교과 7 · 이미지 라벨링 — {name}{' *' if self.dirty else ''}")

    STATUS_HOLD_SECONDS = 5.0      # 저장 결과·경고 같은 메시지를 마우스 좌표 안내가 덮지 못하게 지켜 주는 시간

    def set_status(self, text):
        """상태줄에 결과·안내 메시지를 보인다. 몇 초 동안은 마우스 움직임으로 생기는 좌표 안내가 덮어쓰지 못한다."""
        self.status.config(text=text)
        self._status_hold_until = time.monotonic() + self.STATUS_HOLD_SECONDS

    def hover_status(self, text):
        """마우스를 움직일 때 나오는 좌표·조작 안내. 최근에 결과 메시지가 있었다면 그 메시지가 사라지지 않도록 건너뛴다."""
        if time.monotonic() >= self._status_hold_until:
            self.status.config(text=text)

    # ====================================================================
    # 좌표 변환 (원본 픽셀 ↔ 화면)   ★ 이 두 줄을 이해하면 라벨링 프로그램의 절반을 이해한 것
    #    실제 계산은 Viewport 가 한다 (확대·이동해도 같은 식).
    # ====================================================================

    def to_screen(self, x, y):
        """원본 이미지 픽셀 → 캔버스 화면 좌표.   화면 = 원본 × scale + offset"""
        return self.vp.image_to_canvas(x, y)

    def to_image(self, sx, sy):
        """캔버스 화면 좌표 → 원본 이미지 픽셀.   원본 = (화면 − offset) ÷ scale"""
        return self.vp.canvas_to_image(sx, sy)

    # ====================================================================
    # ③ 확대 / 축소 / 화면 이동
    # ====================================================================

    def zoom(self, factor, cx=None, cy=None):
        """(cx, cy) 화면 지점을 기준으로 확대/축소. 위치를 안 주면 캔버스 가운데 기준."""
        if self.pil_image is None or self.drag:
            return False
        if cx is None:
            cw, ch = self.canvas_size()
            cx, cy = cw / 2, ch / 2
        if not self.vp.zoom_at(factor, cx, cy):
            self.set_status(f"더 이상 {'확대' if factor > 1 else '축소'}할 수 없습니다. ({self.vp.zoom_percent}%)")
            return False
        self.auto_fit = False
        self.render()
        self.set_status(f"배율 {self.vp.zoom_percent}%   |   휠 = 확대/축소 · 오른쪽 드래그 = 이동 · F = 화면 맞춤")
        return True

    def zoom_in(self):
        return self.zoom(ZOOM_STEP)

    def zoom_out(self):
        return self.zoom(1 / ZOOM_STEP)

    def fit_to_window(self):
        """[⤢ 맞춤] / F / Ctrl+0 : 이미지 전체가 보이도록 되돌린다."""
        if self.pil_image is None:
            return
        self.show_image()
        self.set_status(f"화면 맞춤 — 배율 {self.vp.zoom_percent}%")

    def on_mouse_wheel(self, event):
        """휠 위 = 확대, 휠 아래 = 축소.  커서 아래 지점이 제자리에 머문다."""
        up = getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0
        self.zoom(ZOOM_STEP if up else 1 / ZOOM_STEP, event.x, event.y)
        return "break"

    def on_pan_start(self, event):
        if self.pil_image is None or self.drag:
            return
        self.pan_last = (event.x, event.y)
        self.set_cursor("fleur")

    def on_pan_drag(self, event):
        """이동하는 동안은 이미 그려진 것을 그대로 옮기고(빠름), 잠깐 멈추면 빈 곳까지 다시 그린다."""
        if self.pan_last is None:
            return
        dx, dy = event.x - self.pan_last[0], event.y - self.pan_last[1]
        self.pan_last = (event.x, event.y)
        if dx == 0 and dy == 0:
            return
        self.vp.pan(dx, dy)
        self.auto_fit = False
        self.canvas.move("img", dx, dy)
        self.canvas.move("box", dx, dy)
        if self._render_job is not None:
            self.root.after_cancel(self._render_job)
        self._render_job = self.root.after(40, self.render)

    def on_pan_end(self, _event):
        if self.pan_last is None:
            return
        self.pan_last = None
        self.set_cursor("fleur" if self.pan_var.get() else "crosshair")
        if self._render_job is not None:
            self.root.after_cancel(self._render_job)
        self.render()

    # ====================================================================
    # 마우스 이벤트 ([Tkinter 개념 5: 함수 = 할 일 목록])
    #    누름(Press) → 움직임(Drag) → 뗌(Release) 세 단계로 BBox 를 만든다.
    # ====================================================================

    HANDLE_TOL_PX = 8        # 핸들을 잡을 수 있는 화면 거리 (픽셀)

    def on_mouse_down(self, event):
        """① 누른 순간 — 무엇을 하려는지 정한다.
        · 선택된 BBox 의 핸들 위       → 크기 조절
        · BBox 안쪽                     → 그 BBox 를 선택하고 이동 준비 (움직이지 않고 떼면 '선택'만 된 것)
        · 빈 곳, 또는 Shift 를 누른 채  → 새 BBox 그리기 (Shift 는 기존 BBox 위에서 새 BBox 를 그릴 때)"""
        self.canvas.focus_set()              # 입력칸에 있던 커서를 가져온다 → 숫자키·Delete 단축키가 다시 동작
        if self.pil_image is None or self.pan_last is not None:
            return
        if self.pan_var.get():                                #  이동 모드: 왼쪽 버튼으로 화면을 옮긴다
            self.on_pan_start(event)
            return
        if not self.show_boxes_var.get():
            self.set_status("BBox 가 숨겨져 있어요 — H 키(또는 'BBox 보기')로 다시 보이게 한 뒤 편집하세요.")
            return
        ix, iy = self.to_image(event.x, event.y)
        if not getattr(event, "state", 0) & 0x0001:          # 0x0001 = Shift
            if self.selected is not None:
                handle = hit_handle(self.boxes[self.selected], ix, iy, self.HANDLE_TOL_PX / self.vp.scale)
                if handle:
                    self.start_edit("resize", self.selected, event, handle)
                    return
            idx = find_box_at(self.boxes, ix, iy)
            if idx is not None:
                if idx != self.selected:
                    self.select_box(idx)
                self.start_edit("move", idx, event)
                return
        rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                            outline="#ffeb3b", dash=(4, 2), width=2, tags="rubber")
        self.drag = {"mode": "new", "x0": event.x, "y0": event.y, "rect": rect}

    def start_edit(self, mode, index, event, handle=None):
        """이동 / 크기 조절 시작. 원래 BBox 를 기억해 두면 Esc 로 취소하거나 Undo 기록을 만들 수 있다."""
        ix, iy = self.to_image(event.x, event.y)
        self.drag = {"mode": mode, "index": index, "orig": dict(self.boxes[index]), "handle": handle,
                     "ix": ix, "iy": iy, "start": (event.x, event.y), "moved": False}
        self.set_cursor(HANDLE_CURSORS[handle] if handle else "fleur")

    def on_mouse_drag(self, event):
        """② 누른 채 움직이는 동안 — 새 BBox 의 점선 사각형을 늘리거나, BBox 를 옮기고 크기를 바꾼다."""
        self.update_cross(event.x, event.y)
        if self.pan_last is not None:                         #  이동 모드로 끄는 중
            self.on_pan_drag(event)
            return
        d = self.drag
        if not d:
            return
        if d["mode"] == "new":
            self.canvas.coords(d["rect"], d["x0"], d["y0"], event.x, event.y)
            return
        if not d["moved"] and max(abs(event.x - d["start"][0]), abs(event.y - d["start"][1])) < MIN_DRAG_PX:
            return                           # 클릭하다가 살짝 흔들린 정도는 이동으로 치지 않는다
        d["moved"] = True
        ix, iy = self.to_image(event.x, event.y)
        if d["mode"] == "move":
            new = move_box(d["orig"], ix - d["ix"], iy - d["iy"], self.img_w, self.img_h)
        else:
            new = resize_box(d["orig"], d["handle"], ix, iy, self.img_w, self.img_h)
        self.boxes[d["index"]] = new
        self.draw_boxes()                    # BBox 만 다시 그린다 (가벼움)

    def on_mouse_up(self, event):
        """③ 뗀 순간 — 이동·크기 조절을 확정하거나, '클릭'이면 선택, '드래그'면 새 BBox 생성."""
        if self.pan_last is not None:                         #  이동 모드로 끌던 것을 마친다
            self.on_pan_end(event)
            return
        d, self.drag = self.drag, None
        if not d:
            return
        if d["mode"] != "new":
            self.finish_edit(d)
            return
        self.canvas.delete(d["rect"])                        # 임시 사각형 제거

        dx, dy = abs(event.x - d["x0"]), abs(event.y - d["y0"])
        if dx < MIN_DRAG_PX and dy < MIN_DRAG_PX:            # 거의 안 움직였다 = 클릭
            self.select_box(find_box_at(self.boxes, *self.to_image(event.x, event.y)))
            return
        if dx < MIN_DRAG_PX or dy < MIN_DRAG_PX:             # 한쪽만 너무 얇다 = 실수 드래그
            self.set_status("너무 얇게 드래그해서 BBox 를 만들지 않았습니다.")
            return

        # 화면 좌표 → 원본 픽셀 좌표 로 바꾼 뒤, BBox 로 만든다 (이미지 밖 자르기·정렬·최소 크기 검사 포함)
        ax, ay = self.to_image(d["x0"], d["y0"])
        bx, by = self.to_image(event.x, event.y)
        box = make_box(self.current_class, ax, ay, bx, by, self.img_w, self.img_h)
        if box is None:
            self.set_status("이미지 밖이거나 너무 작은 영역이라 BBox 를 만들지 않았습니다.")
            return
        if self.current_class in settings.UNUSED_CLASSES:    # 사용 안 하는 Class 로는 새 BBox 를 만들지 않는다
            messagebox.showwarning("사용 안 함", f"Class {self.current_class}({settings.class_name(self.current_class, False)})는 "
                                   "이번 프로젝트에서 사용하지 않습니다.\n다른 Class 를 선택하세요.")
            return

        self.history.push(self.boxes)                        # ★ 바꾸기 '직전' 상태를 Undo 기록에 남긴다
        self.boxes.append(box)
        self.selected = len(self.boxes) - 1                  # 방금 만든 BBox 를 선택 상태로
        self.mark_changed()

    def finish_edit(self, d):
        """이동·크기 조절을 마친다. 실제로 바뀌었으면 Undo 기록(바뀌기 '전' 상태)을 남긴다."""
        idx = d["index"]
        if not d["moved"] or idx >= len(self.boxes) or self.boxes[idx] == d["orig"]:
            if idx < len(self.boxes):
                self.boxes[idx] = d["orig"]                  # 바뀐 게 없으면 원래 그대로
            self.draw_boxes()
            return
        before = [dict(b) for b in self.boxes]
        before[idx] = dict(d["orig"])                        # 지금 목록에서 이 BBox 만 원래 값으로 → '바뀌기 전' 상태
        self.history.push(before)
        what = "이동" if d["mode"] == "move" else "크기 조절"
        self.mark_changed()
        self.set_status(f"BBox {idx + 1}번 {what} — Ctrl+Z 로 되돌릴 수 있습니다.")

    def cancel_drag(self):
        """Esc — 하던 드래그(새 BBox·이동·크기 조절)를 취소한다. 취소할 게 있었으면 True."""
        d, self.drag = self.drag, None
        if not d:
            return False
        if d["mode"] == "new":
            self.canvas.delete(d["rect"])
        else:
            if d["index"] < len(self.boxes):
                self.boxes[d["index"]] = d["orig"]           # 원래 값으로 되돌림 (Undo 기록은 만들지 않았다)
            self.draw_boxes()
            self.refresh_box_list()
        self.set_status("취소했습니다.")
        return True

    def on_escape(self):
        """Esc — 드래그 중이면 취소, 아니면 BBox 선택 해제."""
        if not self.cancel_drag() and self.selected is not None:
            self.select_box(None)

    def set_cursor(self, name):
        """마우스 모양을 바꾼다 (이미 같으면 건드리지 않는다). 환경이 모르는 이름이면 'sizing' 으로 대신한다."""
        if name == self._cursor:
            return
        try:
            self.canvas.config(cursor=name)
        except tk.TclError:
            self.canvas.config(cursor="sizing")
        self._cursor = name

    def update_hover_cursor(self, ix, iy):
        """BBox 위에서 마우스 모양: 핸들 = 크기 조절 화살표, 안쪽 = 이동, 그 밖 = 십자."""
        if self.pan_var.get():                                 #  이동 모드에서는 어디서나 손 모양
            self.set_cursor("fleur")
            return
        name = "crosshair"
        if self.selected is not None:
            handle = hit_handle(self.boxes[self.selected], ix, iy, self.HANDLE_TOL_PX / self.vp.scale)
            if handle:
                name = HANDLE_CURSORS[handle]
        if name == "crosshair" and find_box_at(self.boxes, ix, iy) is not None:
            name = "fleur"
        self.set_cursor(name)

    def on_mouse_move(self, event):
        """그냥 움직일 때: 마우스 모양을 바꾸고, 가리키는 '원본 이미지 좌표'를 상태줄에 표시 (좌표 개념 확인용)."""
        self.update_cross(event.x, event.y)
        if self.pil_image is None or self.drag or self.pan_last is not None:
            return
        x, y = self.to_image(event.x, event.y)
        self.update_hover_cursor(x, y)
        if 0 <= x < self.img_w and 0 <= y < self.img_h:
            self.hover_status(f"원본 좌표 ({x:.0f}, {y:.0f})   |   배율 {self.vp.zoom_percent}%   |   "
                            "빈 곳 드래그 = 새 BBox · 안쪽 드래그 = 이동 · 핸들 드래그 = 크기 · Shift+드래그 = 겹쳐서 새 BBox · Esc = 취소")

    def on_canvas_resize(self, event):
        """창 크기를 바꾸는 동안 이 이벤트가 수십 번 쏟아진다.
        매번 이미지를 다시 줄이면 렉이 걸리므로, 마지막 변경 후 0.1초 뒤에 '한 번만' 다시 그린다 (디바운스)."""
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(100, self.on_resize_done)

    def on_resize_done(self):
        """확대하지 않은 상태면 다시 화면 맞춤, 확대 중이면 배율을 유지한 채 다시 그린다."""
        self._resize_job = None
        if self.auto_fit or self.pil_image is None:
            self.show_image()
        else:
            self.render()

    # ====================================================================
    # BBox 선택 / 삭제 / Class 변경
    # ====================================================================

    def select_next_box(self, delta):
        """Tab / Shift+Tab — 다음·이전 BBox 를 선택한다 (끝에서 처음으로 돌아간다). 마우스 없이 BBox 를 차례로 확인할 때."""
        if self.pil_image is None or self.drag:
            return "break"
        if not self.boxes:
            self.set_status("이 사진에는 BBox 가 없습니다.")
            return "break"
        cur = self.selected if self.selected is not None else (-1 if delta > 0 else 0)
        self.select_box((cur + delta) % len(self.boxes))
        return "break"                                           # Tab 이 다른 칸으로 커서를 옮기지 않게

    def nudge(self, dx, dy, big=False):
        """Shift+방향키 — 선택한 BBox 를 원본 픽셀 1px (big 이면 10px) 만큼 옮긴다. 정밀하게 맞출 때."""
        if self.pil_image is None or self.drag:
            return "break"
        if self.selected is None:
            self.set_status("먼저 BBox 를 선택하세요 (클릭 또는 Tab). Shift+방향키로 1px 씩 옮길 수 있습니다.")
            return "break"
        step = 10 if big else 1
        old = self.boxes[self.selected]
        new = move_box(old, dx * step, dy * step, self.img_w, self.img_h)
        if new == old:
            self.set_status("더 이상 그쪽으로 옮길 수 없습니다. (이미지 가장자리)")
            return "break"
        now = time.monotonic()
        if not (self._nudge_idx == self.selected and now - self._nudge_t < 1.0):
            self.history.push(self.boxes)                        # 연달아 누르는 동안은 Undo 한 번으로 되돌아가게 처음에만 기록
        self._nudge_idx, self._nudge_t = self.selected, now
        self.boxes[self.selected] = new
        self.mark_changed()
        self.set_status(f"BBox {self.selected + 1}번 이동 — x1,y1 = ({new['x1']:.0f}, {new['y1']:.0f})   (Ctrl+Z 로 되돌리기)")
        return "break"

    def toggle_boxes(self):
        """H — BBox 를 숨기거나 다시 보인다."""
        self.show_boxes_var.set(not self.show_boxes_var.get())
        self.on_boxes_toggled()

    def on_boxes_toggled(self):
        self.draw_boxes()
        self.set_status("BBox 를 숨겼습니다 — 아래 이물을 그대로 볼 수 있어요. H 키로 다시 보입니다. (숨긴 동안은 BBox 를 그리거나 고칠 수 없습니다)"
                        if not self.show_boxes_var.get() else "BBox 를 다시 보입니다.")

    def select_box(self, index):
        """BBox 선택(None 이면 선택 해제). 선택하면 Class 목록도 그 BBox 의 Class 로 맞춘다."""
        self.selected = index
        if index is not None:
            cls = self.boxes[index]["cls"]
            if 0 <= cls < len(settings.CLASSES):
                self.current_class = cls
                self.class_list.set(cls)
        self.draw_boxes()
        self.refresh_box_list()

    def delete_selected(self):
        """[선택 BBox 삭제] / Delete 키."""
        if self.drag:
            return
        if self.selected is None:
            self.set_status("삭제할 BBox 를 먼저 클릭해서 선택하세요.")
            return
        self.history.push(self.boxes)
        del self.boxes[self.selected]
        self.selected = None
        self.mark_changed()

    def clear_all(self):
        """[전체 삭제] 이 사진의 BBox 를 모두 지운다. 확인창을 거치고, Ctrl+Z 로 되돌릴 수 있다."""
        if self.drag or self.pil_image is None:
            return
        if not self.boxes:
            self.set_status("지울 BBox 가 없습니다.")
            return
        if not messagebox.askyesno("전체 삭제", f"이 사진의 BBox {len(self.boxes)}개를 모두 지울까요?\n\n"
                                   "Ctrl+Z 로 되돌릴 수 있고, [저장]하기 전에는 파일이 바뀌지 않습니다."):
            return
        count = len(self.boxes)
        self.history.push(self.boxes)
        self.boxes.clear()
        self.selected = None
        self.mark_changed()
        self.set_status(f"BBox {count}개를 모두 지웠습니다 — Ctrl+Z 로 되돌릴 수 있습니다.")

    def choose_class(self, cid):
        """Class 선택(숫자키 / 목록 클릭 공통).
        - BBox 가 선택되어 있으면 → 그 BBox 의 Class 를 바꾼다 (기존 라벨의 Class 오류 수정)
        - 선택된 BBox 가 없으면    → 앞으로 새로 그릴 BBox 의 Class 로 쓴다"""
        if cid in settings.UNUSED_CLASSES:
            messagebox.showwarning("사용 안 함", f"Class {cid} ({settings.class_name(cid, False)}) 는 이번 프로젝트에서 사용하지 않습니다.\n"
                                   "판단이 어려우면 REVIEW 로 표시합니다.")
            self.class_list.set(self.current_class)
            return
        self.current_class = cid
        self.class_list.set(cid)
        if self.selected is not None and self.boxes[self.selected]["cls"] != cid:
            self.history.push(self.boxes)
            self.boxes[self.selected]["cls"] = cid
            self.mark_changed()

    def on_box_list_selected(self, _event):
        """표에서 줄을 눌렀을 때 그 BBox 를 선택한다. (표를 다시 채우는 중에 생기는 이벤트는 무시)"""
        if self._box_guard:
            return
        sel = self.box_list.selection()
        if sel and int(sel[0]) != self.selected:
            self.select_box(int(sel[0]))

    def mark_changed(self):
        """BBox 가 바뀐 뒤 공통으로 하는 일: 저장 안 함 표시 + 화면 갱신."""
        self._edit_serial += 1
        self.dirty = True
        self.draw_boxes()
        self.refresh_box_list()
        self.update_title()

    # ====================================================================
    # ③ 되돌리기(Undo) / 다시 실행(Redo)
    # ====================================================================

    def undo(self):
        """[↶ 되돌리기] / Ctrl+Z"""
        if self.drag:                                        # 드래그 도중에는 Esc 로 먼저 끝낸다
            return False
        prev = self.history.undo(self.boxes)
        if prev is None:
            self.set_status("되돌릴 작업이 없습니다.")
            return False
        self.boxes = prev
        self.after_history("되돌리기")
        return True

    def redo(self):
        """[↷ 다시] / Ctrl+Y · Ctrl+Shift+Z"""
        if self.drag:
            return False
        nxt = self.history.redo(self.boxes)
        if nxt is None:
            self.set_status("다시 실행할 작업이 없습니다.")
            return False
        self.boxes = nxt
        self.after_history("다시 실행")
        return True

    def after_history(self, what):
        self._edit_serial += 1
        self._nudge_t = 0.0
        self.selected = None
        self.dirty = self.boxes != self._clean           # 처음 상태까지 되돌리면 '변경 없음'
        self.draw_boxes()
        self.refresh_box_list()
        self.update_title()
        self.set_status(f"{what} — BBox {len(self.boxes)}개   (남은 되돌리기 {len(self.history)}번)")


# ============================================================================
# 실행부 ([Tkinter 개념 6: mainloop])
#    mainloop() = "창을 띄워 놓고 마우스/키보드 이벤트를 계속 기다리는 무한 반복".
#    이 줄이 없으면 창이 잠깐 떴다가 바로 사라진다.
# ============================================================================

def main():
    root = make_root()          # tkinterdnd2 가 있으면 폴더 끌어다 놓기가 켜진다
    Day1Labeler(root)
    root.mainloop()