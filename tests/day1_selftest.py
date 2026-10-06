"""1일차 프로그램 자체 점검 (RAW/WORK 분리, 데이터 조사, End-to-End, RAW 불변, Class 설정을 코드로 확인).

임시 폴더에 '가짜 데이터'를 만들어 시험하므로 data/raw 의 실제 데이터는 읽지도 건드리지도 않는다.

    python tests/day1_selftest.py
"""
import hashlib
import shutil
import sys
import tempfile
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image                                     # noqa: E402

from src import settings                                  # noqa: E402
from src.bbox.bbox_manager import make_box, find_box_at   # noqa: E402
from src.data_paths import locate_in_raw, work_label_path  # noqa: E402
from src.ui import main_window as mw                      # noqa: E402
from src.validation.validator import inventory_markdown, scan_inventory  # noqa: E402
from src.yolo.coords import pixel_to_yolo, yolo_to_pixel  # noqa: E402
from src.yolo.yolo_loader import find_raw_label           # noqa: E402


def ok(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        raise SystemExit(1)


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


# ── Class 설정 (configs/classes.yaml) ───────────────────────────────────────
ok("Class 7개(0~6)를 설정 파일에서 읽는다", [c["id"] for c in settings.CLASSES] == list(range(7)))
ok("Class 이름이 기준 문서와 같다", settings.CLASSES[1]["name"] == "플라스틱류·돌·금속류" and settings.CLASSES[6]["name"] == "파·고추")
ok("Class 4(고무장갑)는 사용 안 함", settings.UNUSED_CLASSES == {4} and "(사용 안 함)" in settings.class_name(4))
ok("설정 파일이 없으면 기본값으로 진행", len(settings.load_classes(Path("/없는/경로.yaml"))) == 7)

# ── 순수 함수 ───────────────────────────────────────────────────────────────
b = yolo_to_pixel(0.5, 0.5, 0.2, 0.1, 1000, 500)
ok("YOLO ↔ 픽셀 좌표 변환 왕복", all(abs(a - c) < 1e-9 for a, c in zip(pixel_to_yolo(*b, 1000, 500), (0.5, 0.5, 0.2, 0.1))))
ok("BBox: 이미지 밖은 잘라내고 정렬한다", make_box(2, 900, 900, -50, -50, 800, 600) == {"cls": 2, "x1": 0, "y1": 0, "x2": 800, "y2": 600})
ok("BBox: 너무 작은 영역은 만들지 않는다", make_box(2, 10, 10, 12, 12, 800, 600) is None)
ok("BBox: 겹치면 안쪽(작은) BBox 를 고른다",
   find_box_at([{"x1": 0, "y1": 0, "x2": 100, "y2": 100}, {"x1": 40, "y1": 40, "x2": 60, "y2": 60}], 50, 50) == 1)

tmp = Path(tempfile.mkdtemp(prefix="day1_selftest_"))
raw, work = tmp / "raw", tmp / "work"
try:
    # ── 가짜 RAW 구조 만들기 (회사 데이터와 같은 모양) ──────────────────────────
    def make(ds, split, name, lines):
        (raw / ds / "images" / split).mkdir(parents=True, exist_ok=True)
        (raw / ds / "labels" / split).mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (800, 600), (170, 200, 110)).save(raw / ds / "images" / split / f"{name}.jpg")
        if lines is not None:
            (raw / ds / "labels" / split / f"{name}.txt").write_text(lines, encoding="utf-8")

    make("DS1", "train", "a", "2 0.5 0.5 0.2 0.2\n3 0.2 0.2 0.1 0.1\n")
    make("DS1", "train", "b", "")                                    # 빈 TXT (정상 김치 후보)
    make("DS2", "validation", "c", "4 0.5 0.5 0.2 0.2\n")            # Class 4
    make("DS2", "validation", "d", None)                             # TXT 없는 JPG
    (raw / "DS2" / "labels" / "validation" / "e.txt").write_text("0 0.5 0.5 0.1 0.1\n")   # JPG 없는 TXT
    raw_hash = {p: md5(p) for p in raw.rglob("*.txt")}

    settings.RAW_DIR, settings.WORK_DIR = raw, work                  # 프로그램이 임시 폴더를 쓰도록 바꿈

    # ── 데이터 조사 ────────────────────────────────────────────────────────────
    rows, summary = scan_inventory(raw)
    got = {(r["dataset"], r["split"]): (r["image"], r["label"], r["pair"], r["empty"]) for r in rows}
    ok("조사: DS1/train = 이미지2 TXT2 짝2 빈1", got[("DS1", "train")] == (2, 2, 2, 1))
    ok("조사: DS2/validation = 이미지2 TXT2 짝1 (짝 안 맞는 파일 발견)", got[("DS2", "validation")] == (2, 2, 1, 0))
    ok("조사: 사용 안 하는 Class 4 의 BBox 1개를 찾아낸다", summary["class_bbox"][4] == 1)
    ok("조사: 마크다운 표가 만들어진다", "| source_dataset |" in inventory_markdown(rows, summary))

    # ── RAW / WORK 구조 매핑 ───────────────────────────────────────────────────
    img_a = raw / "DS1" / "images" / "train" / "a.jpg"
    ok("출처 판별: (DS1, train)", locate_in_raw(img_a) == ("DS1", "train"))
    ok("WORK 경로가 RAW 와 같은 구조", work_label_path(img_a) == work / "DS1" / "labels" / "train" / "a.txt")
    ok("같은 이름 원본 TXT 자동 탐색", find_raw_label(img_a) == raw / "DS1" / "labels" / "train" / "a.txt")

    # ── 이미지 1장 End-to-End ──────────────────────────────────────────────────
    root = tk.Tk()
    app = mw.Day1Labeler(root)
    root.update()
    mw.filedialog.askopenfilename = lambda **k: str(img_a)
    mw.messagebox.showerror = mw.messagebox.showwarning = mw.messagebox.showinfo = lambda *a, **k: None
    app.open_image()
    root.update()
    ok("TXT 자동 Load: BBox 2개", len(app.boxes) == 2)

    class E:
        def __init__(self, x, y):
            self.x, self.y = x, y

    app.choose_class(5)
    app.on_mouse_down(E(150, 120)); app.on_mouse_drag(E(220, 180)); app.on_mouse_up(E(220, 180))
    ok("드래그로 BBox 추가 → 3개, 변경 표시", len(app.boxes) == 3 and app.dirty)
    app.on_mouse_down(E(400, 400)); app.on_mouse_up(E(402, 401))
    ok("2px 실수 드래그는 BBox 가 되지 않는다", len(app.boxes) == 3)
    saved = [dict(b) for b in app.boxes]
    ok("저장 성공", app.save())
    ok("WORK 에 같은 구조로 TXT 생성", (work / "DS1" / "labels" / "train" / "a.txt").is_file())
    app.boxes = []; app.draw_boxes()
    app.reload(); root.update()
    ok("다시 불러오기: 같은 위치·Class 로 복원", len(app.boxes) == 3 and all(
        a["cls"] == b["cls"] and all(abs(a[k] - b[k]) < 1e-3 for k in ("x1", "y1", "x2", "y2"))
        for a, b in zip(app.boxes, saved)))

    # ── RAW 원본 불변 + 쓰기 방지 안전장치 ──────────────────────────────────────
    ok("RAW TXT 는 하나도 바뀌지 않았다 (해시 동일)", {p: md5(p) for p in raw.rglob("*.txt")} == raw_hash)
    app.dirty = True
    original = mw.work_label_path
    mw.work_label_path = lambda p: raw / "DS1" / "labels" / "train" / "a.txt"      # 일부러 RAW 안으로 저장 시도
    ok("안전장치: RAW 안에는 저장을 거부한다", app.save() is False)
    mw.work_label_path = original
    ok("안전장치 시도 후에도 RAW 불변", {p: md5(p) for p in raw.rglob("*.txt")} == raw_hash)

    # ── 빈 TXT / TXT 없음 ──────────────────────────────────────────────────────
    app.dirty = False
    mw.filedialog.askopenfilename = lambda **k: str(raw / "DS1" / "images" / "train" / "b.jpg")
    app.open_image()
    ok("빈 TXT: 오류 없이 BBox 0개 + 안내", len(app.boxes) == 0 and "빈 TXT" in app.status.cget("text"))
    mw.filedialog.askopenfilename = lambda **k: str(raw / "DS2" / "images" / "validation" / "d.jpg")
    app.open_image()
    ok("TXT 없음: 안내 후 빈 상태", len(app.boxes) == 0 and "TXT 가 없어" in app.status.cget("text"))
    root.destroy()
    print("\nALL OK — 자체 점검 통과")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
