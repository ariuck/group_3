"""1일차 프로그램 자체 점검 (RAW/WORK 분리, 데이터 조사, End-to-End, RAW 불변, Class 설정, ③ Zoom·편집을 코드로 확인).

임시 폴더에 '가짜 데이터'를 만들어 시험하므로 data/raw 의 실제 데이터는 읽지도 건드리지도 않는다.

    python tests/day1_selftest.py
"""
import csv
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
from src.manifest.manifest_writer import HEADERS, ManifestError, record_save  # noqa: E402
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


def read_manifest():
    with open(settings.MANIFEST_PATH, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_manifest(rows):
    with open(settings.MANIFEST_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        w.writerows(rows)


HUMAN_COLUMNS = ("이미지 유형", "위치 맞음", "Class 맞음", "누락 객체 여부", "발견된 문제", "작성자", "검수자", "비고(수정 내용)")   # (검수일은 프로그램이 자동으로 적는다)


def near(a, b, eps=1e-6):
    return all(abs(x - y) < eps for x, y in zip(a, b))


def free_drag(app, w=100, h=80, margin=12):
    """화면에서 기존 BBox 와 겹치지 않는 빈 곳에 끌 수 있는 두 점 (시작, 끝)을 찾는다.
    창 크기에 따라 같은 화면 좌표가 기존 BBox 위가 될 수 있어서(그러면 BBox 가 새로 만들어지지 않고 이동한다), 시험이 가끔 실패하던 것을 막는다."""
    cw, ch = app.canvas.winfo_width(), app.canvas.winfo_height()

    def clear(x, y):
        x1, y1 = app.to_image(x - margin, y - margin)
        x2, y2 = app.to_image(x + w + margin, y + h + margin)
        return not any(b["x1"] < x2 and b["x2"] > x1 and b["y1"] < y2 and b["y2"] > y1 for b in app.boxes)

    for y in range(40, max(41, ch - h - 40), 20):
        for x in range(40, max(41, cw - w - 40), 20):
            if clear(x, y):
                return (x, y), (x + w, y + h)
    return (100, 100), (100 + w, 100 + h)


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
    settings.MANIFEST_PATH = tmp / "manifests" / "dataset_manifest.csv"   # 검수표도 임시 폴더에 (처음에는 없음)

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
        def __init__(self, x, y, delta=0, num=None):
            self.x, self.y, self.delta, self.num = x, y, delta, num

    app.choose_class(5)
    app.on_mouse_down(E(150, 120)); app.on_mouse_drag(E(220, 180)); app.on_mouse_up(E(220, 180))
    ok("드래그로 BBox 추가 → 3개, 변경 표시", len(app.boxes) == 3 and app.dirty)
    app.on_mouse_down(E(400, 400)); app.on_mouse_up(E(402, 401))
    ok("2px 실수 드래그는 BBox 가 되지 않는다", len(app.boxes) == 3)
    saved = [dict(b) for b in app.boxes]
    ok("저장 성공", app.save())
    ok("WORK 에 같은 구조로 TXT 생성", (work / "DS1" / "labels" / "train" / "a.txt").is_file())

    # ── 검수표(CSV) 자동 기록 ─────────────────────────────────────────────────
    ok("검수표 CSV 가 처음 저장할 때 만들어진다", settings.MANIFEST_PATH.is_file())
    ok("검수표 머리글이 19칸 기준과 같다", next(csv.reader(open(settings.MANIFEST_PATH, encoding="utf-8-sig"))) == HEADERS and len(HEADERS) == 19)
    rows = read_manifest()
    r = rows[0]
    ok("검수표: 사진 1장 = 1줄", len(rows) == 1 and r["No"] == "1")
    ok("검수표: 파일명·출처·split 이 자동으로 채워진다",
       (r["이미지 파일명"], r["라벨(TXT) 파일명"], r["출처 데이터셋"], r["원래 split"]) == ("a.jpg", "a.txt", "DS1", "train"))
    ok("검수표: 원본 2 → 최종 3, Class 2, 3, 5", (r["원본 BBox 수"], r["최종 BBox 수"], r["Class"]) == ("2", "3", "2, 3, 5"))
    ok("검수표: TXT 줄 수 = 화면 BBox 수 → O", r["TXT 줄 수 = 화면 BBox 수"] == "O")
    ok("검수표: 고쳤으므로 상태가 '수정 완료'", r["상태"] == "수정 완료")
    ok("검수표: 사람이 판단하는 칸은 비어 있다", all(r[h] == "" for h in HUMAN_COLUMNS))
    from datetime import date
    ok("검수표: 검수를 마친 상태(수정 완료)라 검수일에 오늘 날짜가 자동으로 적힌다", r["검수일"] == date.today().isoformat())
    ok("상태줄에 검수표 기록 결과가 보인다", "검수표 기록" in app.status.cget("text"))
    app.boxes = []; app.draw_boxes()
    app.reload(); root.update()
    ok("다시 불러오기: 같은 위치·Class 로 복원", len(app.boxes) == 3 and all(
        a["cls"] == b["cls"] and all(abs(a[k] - b[k]) < 1e-3 for k in ("x1", "y1", "x2", "y2"))
        for a, b in zip(app.boxes, saved)))

    # ── 다시 저장: 새 줄이 아니라 갱신, 사람이 쓴 내용은 보존 ──────────────────────
    app.dirty = True
    ok("다시 저장", app.save())
    rows = read_manifest()
    ok("검수표: 같은 사진은 새 줄이 아니라 갱신 (줄 1개, 원본 수 2 유지)", len(rows) == 1 and rows[0]["원본 BBox 수"] == "2")
    rows[0].update({"상태": "수정 필요", "발견된 문제": "REVIEW: class_ambiguous", "작성자": "A", "비고(수정 내용)": "한글 메모"})
    write_manifest(rows)
    app.load_form()                                  # 검수표를 파일로 고쳤으니 화면 입력칸도 다시 읽는다
    app.boxes.append({"cls": 1, "x1": 10.0, "y1": 10.0, "x2": 60.0, "y2": 60.0})        # 또 고침
    app.dirty = True
    ok("한 번 더 저장", app.save())
    r = read_manifest()[0]
    ok("검수표: 사람이 쓴 칸(작성자·비고·발견된 문제)을 지우지 않는다",
       (r["작성자"], r["비고(수정 내용)"], r["발견된 문제"]) == ("A", "한글 메모", "REVIEW: class_ambiguous"))
    ok("검수표: 사람이 정한 상태 '수정 필요'(REVIEW 표시)를 덮어쓰지 않는다", r["상태"] == "수정 필요")
    ok("검수표: 최종 BBox 수는 갱신된다 (3 → 4)", r["최종 BBox 수"] == "4")
    app.boxes.pop(); app.dirty = False

    # ── RAW 원본 불변 + 쓰기 방지 안전장치 ──────────────────────────────────────
    ok("RAW TXT 는 하나도 바뀌지 않았다 (해시 동일)", {p: md5(p) for p in raw.rglob("*.txt")} == raw_hash)
    app.dirty = True
    original = mw.work_label_path
    mw.work_label_path = lambda p: raw / "DS1" / "labels" / "train" / "a.txt"      # 일부러 RAW 안으로 저장 시도
    ok("안전장치: RAW 안에는 저장을 거부한다", app.save() is False)
    mw.work_label_path = original
    ok("안전장치 시도 후에도 RAW 불변", {p: md5(p) for p in raw.rglob("*.txt")} == raw_hash)

    # ── ③ Zoom · 화면 이동 · Undo/Redo ─────────────────────────────────────────
    app.dirty = False
    mw.filedialog.askopenfilename = lambda **k: str(img_a)
    app.open_image(); root.update()
    n0 = len(app.boxes)
    fit_scale = app.vp.scale
    ok("이미지를 열면 화면 맞춤 상태", app.auto_fit and fit_scale > 0)

    before = app.to_image(300, 250)
    app.on_mouse_wheel(E(300, 250, delta=120)); app.on_mouse_wheel(E(300, 250, num=4))   # Windows 휠 · Linux 휠
    ok("휠 확대: 배율이 커진다", app.vp.scale > fit_scale * 1.5 and not app.auto_fit)
    ok("휠 확대: 커서 아래 지점이 제자리", near(app.to_image(300, 250), before))
    app.on_mouse_wheel(E(300, 250, num=5))
    ok("휠 축소: 배율이 줄어든다", app.vp.scale < fit_scale * 1.5)

    app.zoom_in(); app.zoom_in()
    app.choose_class(3)
    (sx, sy), (ex, ey) = free_drag(app)                                        # 기존 BBox 와 겹치지 않는 빈 곳
    expect = make_box(3, *app.to_image(sx, sy), *app.to_image(ex, ey), app.img_w, app.img_h)
    app.on_mouse_down(E(sx, sy)); app.on_mouse_drag(E(ex, ey)); app.on_mouse_up(E(ex, ey))
    ok("확대 상태에서 그린 BBox 도 원본 픽셀 좌표로 저장", len(app.boxes) == n0 + 1 and app.boxes[-1] == expect)

    ok("Undo: BBox 추가 취소", app.undo() and len(app.boxes) == n0 and not app.dirty)
    ok("Redo: 다시 추가", app.redo() and len(app.boxes) == n0 + 1 and app.dirty)

    app.select_box(0)
    old_cls = app.boxes[0]["cls"]
    new_cls = 6 if old_cls != 6 else 5
    app.choose_class(new_cls)
    ok("Class 변경 후 Undo → 원래 Class", app.boxes[0]["cls"] == new_cls and app.undo() and app.boxes[0]["cls"] == old_cls)

    app.select_box(0)
    app.delete_selected()
    ok("삭제 후 Undo → BBox 복원", len(app.boxes) == n0 and app.undo() and len(app.boxes) == n0 + 1)
    ok("되돌릴 게 없으면 False", all(app.undo() for _ in range(len(app.history))) and app.undo() is False)
    app.redo(); app.redo(); app.redo()

    before = app.to_image(400, 300)
    app.on_pan_start(E(400, 300)); app.on_pan_drag(E(460, 330)); app.on_pan_end(E(460, 330))
    ok("오른쪽 드래그 이동: 이미지가 마우스를 따라간다", near(app.to_image(460, 330), before))

    for _ in range(40):
        app.zoom_in()
    root.update()
    ok("최대 확대에서도 오류 없이 그린다 (보이는 부분만 잘라 그림)", app.vp.zoom_percent == 2000)

    zoomed = [dict(b) for b in app.boxes]
    ok("확대 상태에서 저장", app.save())
    app.fit_to_window(); root.update()
    ok("화면 맞춤으로 복귀", app.auto_fit and abs(app.vp.scale - fit_scale) < 1e-9)
    app.reload(); root.update()
    ok("배율과 상관없이 저장·복원 좌표가 같다", len(app.boxes) == len(zoomed) and all(
        a["cls"] == b["cls"] and all(abs(a[k] - b[k]) < 1e-3 for k in ("x1", "y1", "x2", "y2"))
        for a, b in zip(app.boxes, zoomed)))
    ok("다시 불러오면 Undo 기록은 비워진다", not app.history.can_undo)
    ok("③ 이후에도 RAW 불변", {p: md5(p) for p in raw.rglob("*.txt")} == raw_hash)

    # ── 빈 TXT / TXT 없음 ──────────────────────────────────────────────────────
    app.dirty = False
    mw.filedialog.askopenfilename = lambda **k: str(raw / "DS1" / "images" / "train" / "b.jpg")
    app.open_image()
    ok("빈 TXT: 오류 없이 BBox 0개 + 안내", len(app.boxes) == 0 and "빈 TXT" in app.status.cget("text"))
    mw.filedialog.askopenfilename = lambda **k: str(raw / "DS2" / "images" / "validation" / "d.jpg")
    app.open_image()
    ok("TXT 없음: 안내 후 빈 상태", len(app.boxes) == 0 and "TXT 가 없어" in app.status.cget("text"))

    # ── 검수표: 고치지 않은 사진 / 머리글 보호 / RAW 밖 ─────────────────────────
    mw.filedialog.askopenfilename = lambda **k: str(raw / "DS1" / "images" / "train" / "b.jpg")
    app.open_image()
    ok("고치지 않고 저장", app.save())
    rows = read_manifest()
    b = next(r for r in rows if r["이미지 파일명"] == "b.jpg")
    ok("검수표: 새 줄의 No 가 이어서 매겨진다", b["No"] == "2" and len(rows) == 2)
    ok("검수표: 빈 TXT 는 BBox 수 0 → 0 (빈칸 아님), 줄 수 일치 O", (b["원본 BBox 수"], b["최종 BBox 수"], b["TXT 줄 수 = 화면 BBox 수"]) == ("0", "0", "O"))
    ok("검수표: 고치지 않았으면 '검수 전' (검수 완료는 사람이 표시)", b["상태"] == "검수 전")

    bad = tmp / "bad.csv"
    bad.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    try:
        record_save(img_a, None, work / "DS1" / "labels" / "train" / "a.txt", 1, manifest_path=bad)
        raised = False
    except ManifestError:
        raised = True
    ok("검수표: 머리글이 다르면 덮어쓰지 않고 중단한다", raised and bad.read_text(encoding="utf-8") == "a,b,c\n1,2,3\n")
    ok("검수표: RAW 밖의 이미지는 기록하지 않는다", "RAW 밖" in record_save(tmp / "x.jpg", None, tmp / "x.txt", 0) and len(read_manifest()) == 2)
    root.destroy()
    print("\nALL OK — 자체 점검 통과")
finally:
    shutil.rmtree(tmp, ignore_errors=True)