"""라벨링 화면 (Tkinter) — 이미지 1장 End-to-End.

    [📊 데이터 조사]  → 실제 JPG / TXT 구조 · 개수 · 짝(Pair) · Class 분포를 조사
    [📂 이미지 열기]  → 같은 이름의 TXT 자동 Load → BBox 표시
    BBox 추가 / 삭제 / Class 변경
    [💾 저장]         → WORK 폴더에 "RAW 와 같은 구조"로 저장  (RAW 는 절대 수정하지 않음)
                        + 오른쪽 '검수 기록' 입력칸(상태·작성자·검수자 등)을 검수표(CSV)에 함께 기록
    [🔄 다시 불러오기] → 같은 위치에 BBox 가 복원되는지 확인
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
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk   # Pillow: JPG 를 읽고 화면용으로 줄이는 데 사용

from src import settings
from src.bbox.bbox_manager import MIN_DRAG_PX, find_box_at, make_box
from src.bbox.history import History
from src.bbox.viewport import ZOOM_STEP, Viewport
from src.data_paths import is_inside, locate_in_raw, work_label_path
from src.manifest.manifest_writer import ManifestError, read_human, record_save
from src.ui.form_panel import FormPanel
from src.ui.validation_dialog import show_validation_dialog
from src.validation.validator import inventory_markdown, scan_inventory, validate_dataset, write_report
from src.yolo.yolo_loader import find_raw_label, read_yolo_file
from src.yolo.yolo_writer import write_yolo_file
from src.ui.navigator import ImageNavigator


class Day1Labeler:
    def __init__(self, root):
        self.root = root
        root.title("교과 7 · 이미지 라벨링 (RAW / WORK 구조)")
        root.geometry("1220x780")

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
        self._clean = []           # 마지막으로 불러오거나 저장한 BBox 목록 (Undo 후 '변경 없음' 판단용)

        self.vp = Viewport()       # ★ 화면 = 원본 × scale + offset  (확대·이동 상태를 모두 여기서 관리)
        self.auto_fit = True       # True 면 창 크기가 바뀔 때 다시 '화면 맞춤'. 사용자가 확대/이동하면 False
        self.history = History()   # Undo / Redo 기록
        self.photo = None          # 화면에 그릴 이미지 (ImageTk). 변수에 꼭 붙들고 있어야 사라지지 않는다!

        self.drag = None           # 드래그 중인 정보 (시작점, 임시 사각형 등)
        self.pan_last = None       # 화면 이동(오른쪽 드래그) 중 마지막 마우스 위치
        self._resize_job = None    # 창 크기 변경 후 다시 그리기 예약(디바운스)용
        self._render_job = None    # 화면 이동 중 이미지 다시 그리기 예약용

        self.navigator = ImageNavigator() # 네비게이터 추가

        self.build_widgets()
        self.bind_events()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_image()
        self.set_status(self.start_message())

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
            return "[📊 데이터 조사]로 데이터를 확인하고, [📂 이미지 열기]로 사진 1장을 열어 보세요."
        return "data/raw 폴더에 데이터가 없습니다.  이물검출_학습데이터1·2 의 images / labels 파일을 data/raw 안에 넣어 주세요."

    # ------------------------------------------------------------------
    # 화면 만들기 ([Tkinter 개념 2: 위젯] + [개념 4: command])
    # ------------------------------------------------------------------
    def build_widgets(self):
        # ① 위쪽 버튼 줄.  command=... 에는 '누르면 실행할 함수'를 연결한다.
        #    (주의: command=self.save  처럼 괄호 없이 함수 이름만 넘긴다. 괄호를 붙이면 지금 바로 실행돼 버린다)
        bar = tk.Frame(self.root, padx=6, pady=6)
        bar.pack(side="top", fill="x")
        for text, func in (("📊 데이터 조사", self.show_inventory), ("🔍 무결성 검증(QA)", self.run_validation),
                           ("📁 폴더 열기", self.open_folder), ("📂 이미지 열기", self.open_image),
                           ("💾 저장", self.save), ("🔄 다시 불러오기", self.reload),
                           ("🗑 선택 BBox 삭제", self.delete_selected), ("📁 WORK 폴더 열기", self.open_work_folder)):
            tk.Button(bar, text=text, command=func, padx=8, pady=3).pack(side="left", padx=3)

        # ①-2 오른쪽 끝: 확대·되돌리기 버튼 (오른쪽부터 쌓이므로 역순으로 pack)
        for text, func in (("↷ 다시", self.redo), ("↶ 되돌리기", self.undo), ("⤢ 맞춤", self.fit_to_window),
                           ("－", self.zoom_out), ("＋", self.zoom_in)):
            tk.Button(bar, text=text, command=func, padx=6, pady=3).pack(side="right", padx=2)

        # ② 현재 사진의 출처 정보 (데이터셋 / split / 파일) — Manifest 의 source_dataset, original_split 에 해당
        #    같은 줄 오른쪽에 이전 / 진행률 / 다음 (위 버튼 줄은 꽉 차서 창이 좁으면 밀려나 안 보였다)
        row = tk.Frame(self.root)
        row.pack(side="top", fill="x")
        self.btn_next = tk.Button(row, text="다음 ▶", command=self.go_next, padx=8, pady=1, state="disabled")
        self.btn_next.pack(side="right", padx=(3, 8))
        self.progress = tk.Label(row, text="0 / 0", font=("Malgun Gothic", 11, "bold"), width=10)
        self.progress.pack(side="right")
        self.btn_prev = tk.Button(row, text="◀ 이전", command=self.go_prev, padx=8, pady=1, state="disabled")
        self.btn_prev.pack(side="right", padx=3)
        self.info = tk.Label(row, text="출처: -", anchor="w", padx=10, pady=2, font=("Malgun Gothic", 10, "bold"))
        self.info.pack(side="left", fill="x", expand=True)

        # ③ 아래쪽 상태 표시줄 (먼저 pack 해야 창이 작아져도 안 가려진다)
        self.status = tk.Label(self.root, text="", anchor="w", padx=8, pady=3, relief="sunken")
        self.status.pack(side="bottom", fill="x")

        # ④ 오른쪽 패널: 클래스 선택 + 라벨 목록 + 검수 기록 입력칸
        side = tk.Frame(self.root, width=260, padx=6, pady=4)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)       # 안의 내용 크기에 맞춰 줄어들지 않고 폭 260 유지

        tk.Label(side, text="클래스 선택", font=("Malgun Gothic", 10, "bold")).pack(anchor="w")
        self.class_list = tk.Listbox(side, height=len(settings.CLASSES), exportselection=False,
                                     font=("Malgun Gothic", 10), activestyle="none")
        for c in settings.CLASSES:
            self.class_list.insert("end", f"■ {c['id']}  {settings.class_name(c['id'])}")
            self.class_list.itemconfig(c["id"], foreground=c["color"] if c["enabled"] else "#9e9e9e")
        self.class_list.selection_set(self.current_class)
        self.class_list.pack(fill="x", pady=(0, 10))

        # 검수 기록 입력칸(상태·작성자·검수자·이미지 유형·발견된 문제·비고) — 패널 맨 아래에 둔다.
        # (라벨 목록보다 먼저 pack 해야 창이 작아져도 입력칸이 가려지지 않는다)
        self.form = FormPanel(side, on_change=self.on_form_changed)
        self.form.pack(side="bottom", fill="x", pady=(8, 0))

        tk.Label(side, text="라벨 목록 (BBox)", font=("Malgun Gothic", 10, "bold")).pack(anchor="w")
        self.box_list = tk.Listbox(side, font=("Consolas", 9), activestyle="none", exportselection=False)
        self.box_list.pack(fill="both", expand=True)

        # ④-2 왼쪽 패널: 같은 폴더의 사진 목록. 누르면 바로 그 사진으로 간다 (✓ = WORK 에 저장된 사진)
        left = tk.Frame(self.root, padx=4, pady=4)
        left.pack(side="left", fill="y")
        tk.Label(left, text="사진 목록", font=("Malgun Gothic", 10, "bold")).pack(anchor="w")
        scroll = tk.Scrollbar(left)
        scroll.pack(side="right", fill="y")
        self.file_list = tk.Listbox(left, width=26, font=("Consolas", 9), activestyle="none",
                                    exportselection=False, yscrollcommand=scroll.set)
        self.file_list.pack(side="left", fill="y")
        scroll.config(command=self.file_list.yview)
        self._listed_files = None        # 지금 목록에 보이는 사진들 (폴더가 바뀔 때만 다시 채운다)

        # ⑤ 가운데: 이미지를 보여 줄 도화지(Canvas)
        self.canvas = tk.Canvas(self.root, bg="#2b2b2b", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="left", fill="both", expand=True)

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

        self.class_list.bind("<<ListboxSelect>>", self.on_class_selected)
        self.box_list.bind("<<ListboxSelect>>", self.on_box_list_selected)
        self.file_list.bind("<<ListboxSelect>>", self.on_file_selected)

        r = self.root
        # 입력칸에 글자를 치는 중에는 글자·숫자 단축키가 동작하면 안 된다
        # (비고에 'f'·'-'·'3' 을 쳤는데 화면이 맞춰지거나 축소되거나 Class 가 바뀌면 안 됨)
        r.bind("<Delete>", lambda e: None if self.is_typing(e) else self.delete_selected())
        r.bind("<Control-s>", lambda e: self.save())
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
        # ← → = 이전/다음 사진 (입력칸에서 글자 커서를 옮기는 중에는 사진이 넘어가면 안 된다)
        for key, func in (("<Left>", self.go_prev), ("<Prior>", self.go_prev),
                          ("<Right>", self.go_next), ("<Next>", self.go_next)):   # Prior/Next = PageUp/PageDown
            r.bind(key, lambda e, f=func: None if self.is_typing(e) else f())

        # 방향키(← →) 및 A / D 키로 이전/다음 사진 이동
        for key in ("<Left>", "a", "A"):
            r.bind(key, lambda e: None if self.is_typing(e) else self.go_prev())
        for key in ("<Right>", "d", "D"):
            r.bind(key, lambda e: None if self.is_typing(e) else self.go_next())

    @staticmethod
    def is_typing(event):
        """키를 누른 곳이 글자 입력칸(Entry·Combobox)인가?"""
        return isinstance(event.widget, (tk.Entry, ttk.Entry))


    # ====================================================================
    # 데이터 조사 / 폴더 열기
    # ====================================================================

    def show_inventory(self):
        """[📊 데이터 조사] RAW 폴더의 개수·짝·빈 TXT·Class 분포를 표로 보여 준다."""
        rows, summary = scan_inventory(settings.RAW_DIR)
        if not rows:
            messagebox.showinfo("데이터 조사", f"조사할 데이터가 없습니다.\n\n{settings.RAW_DIR}\n\n"
                                "이 폴더 안에 이물검출_학습데이터1, 이물검출_학습데이터2 폴더(images / labels 포함)를 넣어 주세요.")
            return
        text = inventory_markdown(rows, summary)

        win = tk.Toplevel(self.root)
        win.title("데이터 조사 결과 (RAW 를 읽기만 한 결과)")
        win.geometry("760x560")
        box = tk.Text(win, font=("Consolas", 10), wrap="none")
        box.insert("1.0", text)
        box.config(state="disabled")
        btns = tk.Frame(win, pady=6)
        btns.pack(side="bottom", fill="x")

        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.set_status("조사 표를 복사했습니다. 옵시디언 노트에 붙여 넣으세요 (Ctrl+V).")

        tk.Button(btns, text="📋 표 복사 (마크다운)", command=copy, padx=8).pack(side="left", padx=8)
        tk.Button(btns, text="닫기", command=win.destroy, padx=8).pack(side="left")
        box.pack(fill="both", expand=True)

    def run_validation(self):
        """[🔍 무결성 검증(QA)] 900장 전체 데이터셋 무결성을 정밀 검사하여 결과 다이얼로그를 띄운다."""
        self.set_status("데이터셋 무결성 검사(Validation) 진행 중...")
        self.root.update_idletasks()
        report = validate_dataset(raw_dir=settings.RAW_DIR, work_dir=settings.WORK_DIR)
        
        out_csv = settings.PROJECT_DIR / "reports" / "validation_report.csv"
        write_report(report, out_csv)
        self.set_status(f"검증 완료: 총 {len(report)}건의 결과 (보고서: reports/validation_report.csv)")

        def jump_to_file(rel_path):
            stem = Path(rel_path).stem
            matches = list(settings.RAW_DIR.rglob(f"{stem}.jpg"))
            if matches:
                self.move_to(matches[0])
            else:
                messagebox.showinfo("안내", f"해당 이미지 파일을 찾을 수 없습니다: {rel_path}")

        show_validation_dialog(self.root, report, csv_path=out_csv, on_jump=jump_to_file)

    def open_work_folder(self):
        """[📁 WORK 폴더 열기] 저장 결과를 파일 탐색기에서 확인한다."""
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

    def open_folder(self):
        """[📁 폴더 열기] 데이터 또는 이미지 폴더 선택 → 하위 모든 이미지 자동 스캔 → 첫 장 표시."""
        if not self.confirm_discard():
            return
        folder = filedialog.askdirectory(
            title="데이터/이미지 폴더 선택 (data/raw 또는 images/ 포함 폴더)",
            initialdir=str(settings.RAW_DIR if settings.RAW_DIR.is_dir() else settings.PROJECT_DIR)
        )
        if not folder:
            return
        first_img = self.navigator.load_folder(folder)
        if not first_img:
            messagebox.showinfo("폴더 열기", f"선택한 폴더 안에 JPG 이미지가 없습니다.\n\n{folder}")
            return
        self.load_image(first_img)
        self.set_status(f"폴더를 열었습니다: {Path(folder).name} (총 {self.navigator.total}장)")

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

    def load_image(self, path):
        """이미지 1장을 읽어 화면에 올린다. (저장 여부 확인은 부르는 쪽에서 이미 끝낸 상태)"""
        try:
            img = Image.open(path)
            img.load()
            img = img.convert("RGB")
        except Exception as e:
            messagebox.showerror("이미지를 열 수 없음", f"{path}\n\n{e}")
            return False
        self.image_path = Path(path)
        self.pil_image = img
        self.img_w, self.img_h = img.size
        self.navigator.set_current(self.image_path)   # 목록·번호 갱신
        self.load_boxes()
        self.show_image()                                    # 새 이미지는 항상 '화면 맞춤'으로 시작
        self.update_nav()
        return True

    # ---- 이전 / 다음 ----
    def go_prev(self):
        self.move_to(self.navigator.prev_path())

    def go_next(self):
        self.move_to(self.navigator.next_path())

    def move_to(self, path):
        if path is None or not self.confirm_discard():   # 저장 안 한 변경이 있으면 먼저 물어봄
            return
        self.load_image(path)

    def update_nav(self):
        """진행률 글자와 [이전]/[다음] 버튼 활성 상태를 맞춘다."""
        nav = self.navigator
        self.progress.config(text=nav.progress_text())
        self.btn_prev.config(state="normal" if nav.has_prev() else "disabled")
        self.btn_next.config(state="normal" if nav.has_next() else "disabled")
        self.refresh_file_list()

    def refresh_file_list(self):
        """왼쪽 사진 목록을 채우고 현재 사진을 표시한다."""
        nav, lb = self.navigator, self.file_list
        if self._listed_files != nav.files:
            self._listed_files = list(nav.files)
            lb.delete(0, "end")
            for p in nav.files:
                lb.insert("end", f"{'✓' if work_label_path(p).exists() else ' '} {p.name}")
        elif self.image_path is not None and 0 <= nav.index < lb.size():   # 방금 저장했으면 ✓ 표시
            lb.delete(nav.index)
            lb.insert(nav.index, f"{'✓' if work_label_path(self.image_path).exists() else ' '} {self.image_path.name}")
        lb.selection_clear(0, "end")
        if 0 <= nav.index < lb.size():
            lb.selection_set(nav.index)
            lb.see(nav.index)

    def on_file_selected(self, _event):
        sel = self.file_list.curselection()
        if not sel or sel[0] == self.navigator.index:
            return
        self.move_to(self.navigator.files[sel[0]])
        self.refresh_file_list()          # 저장 확인에서 [취소]했으면 원래 사진에 표시를 되돌린다

    def load_boxes(self):
        """TXT 를 읽어 self.boxes 에 채운다.

        우선순위:  ① WORK 에 이미 저장한 TXT  →  ② RAW(원본) TXT  →  ③ 없으면 빈 목록
        ① 이 있으면 '내가 지난번에 고친 결과'를 이어서 작업한다.
        """
        self.boxes, self.selected, self.dirty = [], None, False
        self._clean = []
        self.history.clear()                                 # 다른 이미지(또는 다시 불러오기)면 Undo 기록은 버린다
        dataset, split = locate_in_raw(self.image_path)
        where = f"{dataset} / {split}" if dataset else "RAW 밖의 파일"
        self.info.config(text=f"출처: {where}   |   {self.image_path.name}   ({self.img_w}×{self.img_h})")
        self.load_form()

        work = work_label_path(self.image_path)
        source = work if work.is_file() else find_raw_label(self.image_path)
        if source is None:
            self.set_status("TXT 가 없어 BBox 없이 시작합니다. (정상 이미지거나 라벨이 빠진 것일 수 있어요 → 이미지를 직접 확인)")
            return
        self.boxes, bad = read_yolo_file(source, self.img_w, self.img_h)
        self._clean = [dict(b) for b in self.boxes]
        kind = "WORK(내가 저장한 것)" if source == work else "RAW(원본)"
        msg = f"{kind} TXT 에서 BBox {len(self.boxes)}개 로드: {source.name}"
        if not self.boxes and not bad:
            msg += "  ← 빈 TXT: 이물이 정말 없는지 이미지를 보고 확인하세요"
        if bad:
            msg += f"  ⚠ 읽지 못한 줄 {bad}개 (저장하면 WORK 파일에서는 빠집니다)"
        self.set_status(msg)

    def save(self):
        """[저장] WORK 폴더에 YOLO TXT 로 저장.  RAW 는 절대 건드리지 않는다."""
        if self.pil_image is None:
            return False
        target = work_label_path(self.image_path)
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
        self._clean = [dict(b) for b in self.boxes]
        self.update_title()
        self.load_form()                     # 프로그램이 정한 상태(예: 수정 완료)를 입력칸에 다시 보여 준다
        self.refresh_file_list()             # 사진 목록에 ✓ 표시
        self.set_status(f"저장 완료 → {target}   |   {note}")
        return True

    def load_form(self):
        """검수표에 적혀 있던 상태·사람 칸을 입력칸에 보여 준다. (기록이 없으면 빈칸)"""
        try:
            values = read_human(self.image_path)
        except ManifestError as e:
            self.form.clear()
            messagebox.showwarning("검수표 읽기 실패", f"검수표(CSV)를 읽지 못해 입력칸을 비워 둡니다.\n\n{e}")
            return
        self.form.set_values(values)

    def on_form_changed(self):
        """입력칸을 고쳤을 때: 저장 안 한 변경으로 표시한다. (사진을 열기 전에는 저장할 곳이 없으므로 무시)"""
        if self.pil_image is None:
            return
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

    def confirm_discard(self):
        """저장 안 한 변경이 있으면 물어본다. True = 계속 진행해도 됨."""
        if not self.dirty:
            return True
        ans = messagebox.askyesnocancel("저장하지 않은 변경", "저장하지 않은 변경이 있습니다.\n저장할까요?")
        if ans is None:
            return False                     # 취소
        return self.save() if ans else True  # 예 → 저장 / 아니오 → 변경 버림

    def on_close(self):
        if self.confirm_discard():
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
            c.create_text(c.winfo_width() / 2, c.winfo_height() / 2, tags="img", fill="#bbbbbb",
                          font=("Malgun Gothic", 14), justify="center",
                          text="[📂 이미지 열기] 로 시작하세요\n(데이터는 data/raw 폴더에 넣어 두세요)")
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
            part = self.pil_image.crop((x0, y0, x1, y1)).resize((disp_w, disp_h), resample)
            self.photo = ImageTk.PhotoImage(part)            # self.photo 에 저장해 두지 않으면 화면에서 사라진다!
            sx, sy = self.vp.image_to_canvas(x0, y0)
            c.create_image(round(sx), round(sy), anchor="nw", image=self.photo, tags="img")
            c.tag_lower("img")                               # 이미지는 맨 아래, BBox 가 그 위에 오도록
        else:
            self.photo = None                                # 이미지가 화면 밖으로 완전히 나감
        self.draw_boxes()

    def draw_boxes(self):
        """BBox 만 다시 그린다 (가벼움). 원본 픽셀 좌표 → 화면 좌표 변환이 핵심."""
        c = self.canvas
        c.delete("box")
        for i, b in enumerate(self.boxes):
            x1, y1, x2, y2 = self.vp.box_to_canvas(b)
            color = settings.class_color(b["cls"])
            is_sel = (i == self.selected)
            c.create_rectangle(x1, y1, x2, y2, outline=("#ffeb3b" if is_sel else color),
                               width=(4 if is_sel else 2), tags="box")
            tag = c.create_text(x1 + 3, y1 - 2 if y1 > 16 else y1 + 12, anchor=("sw" if y1 > 16 else "nw"),
                                text=f"{b['cls']} {settings.class_name(b['cls'], with_note=False)}", fill="white",
                                font=("Malgun Gothic", 9, "bold"), tags="box")
            bg = c.create_rectangle(c.bbox(tag), fill=color, outline=color, tags="box")
            c.tag_raise(tag, bg)                             # 글자가 배경 사각형 위에 오도록

    def refresh_box_list(self):
        """오른쪽 '라벨 목록'을 현재 self.boxes 와 맞춘다."""
        self.box_list.delete(0, "end")
        for i, b in enumerate(self.boxes):
            w, h = b["x2"] - b["x1"], b["y2"] - b["y1"]
            self.box_list.insert("end", f"{i + 1:>2}  cls {b['cls']}  [{b['x1']:.0f},{b['y1']:.0f},{w:.0f},{h:.0f}]")
        if self.selected is not None and self.selected < len(self.boxes):
            self.box_list.selection_set(self.selected)       # (코드로 선택해도 ListboxSelect 이벤트는 안 생긴다)

    def update_title(self):
        name = self.image_path.name if self.image_path else ""
        self.root.title(f"교과 7 · 이미지 라벨링 — {name}{' *' if self.dirty else ''}")

    def set_status(self, text):
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
        self.canvas.config(cursor="fleur")

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
        self.canvas.config(cursor="crosshair")
        if self._render_job is not None:
            self.root.after_cancel(self._render_job)
        self.render()

    # ====================================================================
    # 마우스 이벤트 ([Tkinter 개념 5: 함수 = 할 일 목록])
    #    누름(Press) → 움직임(Drag) → 뗌(Release) 세 단계로 BBox 를 만든다.
    # ====================================================================

    def on_mouse_down(self, event):
        """① 누른 순간: 시작 위치를 기억하고, 점선 임시 사각형을 만든다."""
        self.canvas.focus_set()              # 입력칸에 있던 커서를 가져온다 → 숫자키·Delete 단축키가 다시 동작
        if self.pil_image is None or self.pan_last is not None:
            return
        rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                            outline="#ffeb3b", dash=(4, 2), width=2, tags="rubber")
        self.drag = {"x0": event.x, "y0": event.y, "rect": rect}

    def on_mouse_drag(self, event):
        """② 누른 채 움직이는 동안: 임시 사각형 크기를 마우스에 맞춰 늘린다."""
        if self.drag:
            self.canvas.coords(self.drag["rect"], self.drag["x0"], self.drag["y0"], event.x, event.y)

    def on_mouse_up(self, event):
        """③ 뗀 순간: '클릭'이면 BBox 선택, '드래그'면 새 BBox 생성."""
        d, self.drag = self.drag, None
        if not d:
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

    def on_mouse_move(self, event):
        """그냥 움직일 때: 마우스가 가리키는 '원본 이미지 좌표'를 상태줄에 표시 (좌표 개념 확인용)."""
        if self.pil_image is None or self.drag or self.pan_last is not None:
            return
        x, y = self.to_image(event.x, event.y)
        if 0 <= x < self.img_w and 0 <= y < self.img_h:
            self.set_status(f"원본 좌표 ({x:.0f}, {y:.0f})   |   배율 {self.vp.zoom_percent}%   |   "
                            "드래그 = BBox · 클릭 = 선택 · 휠 = 확대 · 오른쪽 드래그 = 이동 · F = 맞춤 · Ctrl+Z = 되돌리기")

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

    def select_box(self, index):
        """BBox 선택(None 이면 선택 해제). 선택하면 Class 목록도 그 BBox 의 Class 로 맞춘다."""
        self.selected = index
        if index is not None:
            cls = self.boxes[index]["cls"]
            if 0 <= cls < len(settings.CLASSES):
                self.current_class = cls
                self.class_list.selection_clear(0, "end")
                self.class_list.selection_set(cls)
        self.draw_boxes()
        self.refresh_box_list()

    def delete_selected(self):
        """[선택 BBox 삭제] / Delete 키."""
        if self.selected is None:
            self.set_status("삭제할 BBox 를 먼저 클릭해서 선택하세요.")
            return
        self.history.push(self.boxes)
        del self.boxes[self.selected]
        self.selected = None
        self.mark_changed()

    def choose_class(self, cid):
        """Class 선택(숫자키 / 목록 클릭 공통).
        - BBox 가 선택되어 있으면 → 그 BBox 의 Class 를 바꾼다 (기존 라벨의 Class 오류 수정)
        - 선택된 BBox 가 없으면    → 앞으로 새로 그릴 BBox 의 Class 로 쓴다"""
        if cid in settings.UNUSED_CLASSES:
            messagebox.showwarning("사용 안 함", f"Class {cid} ({settings.class_name(cid, False)}) 는 이번 프로젝트에서 사용하지 않습니다.\n"
                                   "판단이 어려우면 REVIEW 로 표시합니다.")
            self.class_list.selection_clear(0, "end")
            self.class_list.selection_set(self.current_class)
            return
        self.current_class = cid
        self.class_list.selection_clear(0, "end")
        self.class_list.selection_set(cid)
        if self.selected is not None and self.boxes[self.selected]["cls"] != cid:
            self.history.push(self.boxes)
            self.boxes[self.selected]["cls"] = cid
            self.mark_changed()

    def on_class_selected(self, _event):
        sel = self.class_list.curselection()
        if sel:
            self.choose_class(sel[0])

    def on_box_list_selected(self, _event):
        sel = self.box_list.curselection()
        if sel and sel[0] != self.selected:
            self.select_box(sel[0])

    def mark_changed(self):
        """BBox 가 바뀐 뒤 공통으로 하는 일: 저장 안 함 표시 + 화면 갱신."""
        self.dirty = True
        self.draw_boxes()
        self.refresh_box_list()
        self.update_title()

    # ====================================================================
    # ③ 되돌리기(Undo) / 다시 실행(Redo)
    # ====================================================================

    def undo(self):
        """[↶ 되돌리기] / Ctrl+Z"""
        prev = self.history.undo(self.boxes)
        if prev is None:
            self.set_status("되돌릴 작업이 없습니다.")
            return False
        self.boxes = prev
        self.after_history("되돌리기")
        return True

    def redo(self):
        """[↷ 다시] / Ctrl+Y · Ctrl+Shift+Z"""
        nxt = self.history.redo(self.boxes)
        if nxt is None:
            self.set_status("다시 실행할 작업이 없습니다.")
            return False
        self.boxes = nxt
        self.after_history("다시 실행")
        return True

    def after_history(self, what):
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
    root = tk.Tk()
    Day1Labeler(root)
    root.mainloop()