"""화면에서 BBox 를 옮기고 크기를 바꾸는 동작 시험 (마우스 이벤트를 흉내 낸다).

화면(Tk)이 필요하다.  실행 (프로젝트 폴더에서):  python -m unittest tests/test_edit_ui.py
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src import settings

IMG_W, IMG_H = 1000, 600


class Ev:
    """마우스 이벤트 흉내 (x, y = 화면 좌표, state=1 이면 Shift)."""
    def __init__(self, x, y, state=0):
        self.x, self.y, self.state = x, y, state


def make_app():
    from src.ui import main_window as mw
    tmp = Path(tempfile.mkdtemp())
    ds = tmp / "raw" / "DS1"
    (ds / "images" / "train").mkdir(parents=True)
    (ds / "labels" / "train").mkdir(parents=True)
    Image.new("RGB", (IMG_W, IMG_H), "green").save(ds / "images" / "train" / "a.jpg")
    (ds / "labels" / "train" / "a.txt").write_text("2 0.5 0.5 0.2 0.2\n")            # x 400~600, y 240~360
    settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = tmp / "raw", tmp / "work", tmp / "m.csv"
    mw.messagebox.showwarning = mw.messagebox.showerror = mw.messagebox.showinfo = lambda *a, **k: None
    root = mw.make_root()
    app = mw.Day1Labeler(root)
    root.geometry("1200x800")
    root.update()
    app.load_image(str(ds / "images" / "train" / "a.jpg"))
    root.update()
    return root, app, tmp


class EditUiTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root, self.app, tmp = make_app()
            self.addCleanup(shutil.rmtree, tmp, True)
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")

    def tearDown(self):
        for job in (self.app._resize_job, self.app._render_job, self.app._nav_job):
            if job is not None:
                self.root.after_cancel(job)
        self.root.destroy()

    # 원본 픽셀 → 이벤트
    def at(self, x, y, state=0):
        sx, sy = self.app.vp.image_to_canvas(x, y)
        return Ev(sx, sy, state)

    def box(self, i=0):
        b = self.app.boxes[i]
        return tuple(round(b[k], 1) for k in ("x1", "y1", "x2", "y2"))

    def test_handles_are_drawn_only_for_the_selected_box(self):
        c = self.app.canvas
        self.assertEqual(len(c.find_withtag("handle")), 0)
        self.app.select_box(0)
        self.assertEqual(len(c.find_withtag("handle")), 8)
        self.app.on_mouse_down(self.at(500, 300)); self.app.on_mouse_drag(self.at(560, 300))
        self.assertEqual(len(c.find_withtag("handle")), 8)         # 끄는 동안에도 따라다닌다
        self.app.on_mouse_up(self.at(560, 300))
        self.app.select_box(None)
        self.assertEqual(len(c.find_withtag("handle")), 0)

    def test_coordinate_bar_follows_the_selection_and_the_drag(self):
        info = self.app.bbox_info
        self.assertIn("선택된 BBox 없음", info.cget("text"))
        self.app.select_box(0)
        text = info.cget("text")
        for part in ("x1,y1=(400, 240)", "x2,y2=(600, 360)", "W×H=200×120", "xc=0.5000", "yc=0.5000", "w=0.2000", "h=0.2000"):
            self.assertIn(part, text)
        self.app.on_mouse_down(self.at(500, 300)); self.app.on_mouse_drag(self.at(600, 300))
        self.assertIn("x1,y1=(500, 240)", info.cget("text"))      # 끄는 동안 실시간으로 바뀐다
        self.app.on_mouse_up(self.at(600, 300))
        self.app.select_box(None)
        self.assertIn("선택된 BBox 없음", info.cget("text"))

    # ── 화면 보정 (밝기·대비·흑백) ────────────────────────────
    def test_enhance_changes_only_the_copy(self):
        src = Image.new("RGB", (4, 4), (100, 150, 50))
        self.assertEqual(self.app.enhance(src).getpixel((0, 0)), (100, 150, 50))     # 보정 전에는 그대로
        self.app.bright_idx = 1                                                       # ×1.3
        bright = self.app.enhance(src).getpixel((0, 0))
        self.assertGreater(bright[0], 100)
        self.app.bright_idx = 3                                                       # ×0.7
        self.assertLess(self.app.enhance(src).getpixel((0, 0))[0], 100)
        self.app.bright_idx, self.app.gray = 0, True
        r, g, b = self.app.enhance(src).getpixel((0, 0))
        self.assertTrue(r == g == b)                                                  # 흑백
        self.assertEqual(src.getpixel((0, 0)), (100, 150, 50))                        # 입력 사본은 안 바뀐다

    def test_buttons_cycle_and_return_to_normal(self):
        for _ in range(4):
            self.app.cycle_brightness()
        self.assertEqual(self.app.bright_idx, 0)
        self.assertEqual(self.app.btn_bright.cget("text"), "밝기 ×1.0")
        self.app.cycle_contrast()
        self.assertEqual(self.app.btn_contrast.cget("text"), "대비 ×1.3")
        self.app.toggle_gray()
        self.assertEqual(self.app.btn_gray.cget("relief"), "sunken")
        self.app.toggle_gray()
        self.assertEqual(self.app.btn_gray.cget("relief"), "raised")

    def test_enhance_never_changes_the_photo_or_the_saved_label(self):
        from src.data_paths import work_label_path
        before = self.app.pil_image.getpixel((10, 10))
        self.app.cycle_brightness(); self.app.cycle_contrast(); self.app.toggle_gray()
        self.assertEqual(self.app.pil_image.getpixel((10, 10)), before)               # 원본 이미지 객체 그대로
        self.assertFalse(self.app.dirty)                                              # 보정은 '변경'이 아니다
        self.app.save()
        parts = work_label_path(self.app.image_path).read_text().split()
        self.assertAlmostEqual(float(parts[1]), 0.5, places=6)                        # 라벨 좌표 그대로

    # ── 십자선 ────────────────────────────────────────────────
    def cross_items(self):
        return len(self.app.canvas.find_withtag("cross"))

    def test_crosshair_follows_the_mouse_only_when_on(self):
        self.app.on_mouse_move(self.at(100, 100))
        self.assertEqual(self.cross_items(), 0)                   # 기본은 꺼짐
        self.app.cross_var.set(True); self.app.on_cross_toggled()
        self.app.on_mouse_move(self.at(100, 100))
        self.assertEqual(self.cross_items(), 2)                   # 가로선 + 세로선
        self.app.on_mouse_move(self.at(200, 150))
        self.assertEqual(self.cross_items(), 2)                   # 따라다니되 늘어나지 않는다
        x = self.app.canvas.coords(self.app.canvas.find_withtag("cross")[1])[0]
        self.assertAlmostEqual(x, self.at(200, 150).x)

    def test_crosshair_stays_during_a_drag_and_goes_away_when_turned_off(self):
        self.app.cross_var.set(True); self.app.on_cross_toggled()
        self.app.on_mouse_down(self.at(50, 50)); self.app.on_mouse_drag(self.at(120, 120))
        self.assertEqual(self.cross_items(), 2)
        self.app.on_mouse_up(self.at(120, 120))
        self.app.cross_var.set(False); self.app.on_cross_toggled()
        self.assertEqual(self.cross_items(), 0)

    # ── 라벨 목록 표 ───────────────────────────────────────────
    def rows(self):
        lb = self.app.box_list
        return [lb.item(i, "values") for i in lb.get_children()]

    def test_label_table_shows_original_and_changed(self):
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(str(rows[0][0]), "1")
        self.assertIn("2", rows[0][1])                              # Class 번호 + 이름
        self.assertEqual(rows[0][2], "[400,240,200,120]")
        self.assertEqual(rows[0][3], "원본")
        self.assertIn("(1개)", self.app.box_title.cget("text"))

    def test_label_table_marks_a_moved_or_new_box_as_changed(self):
        self.app.on_mouse_down(self.at(500, 300)); self.app.on_mouse_drag(self.at(560, 300))
        self.app.on_mouse_up(self.at(560, 300))
        self.assertEqual(self.rows()[0][3], "변경")
        self.assertEqual(self.rows()[0][2], "[460,240,200,120]")
        self.assertIn("changed", self.app.box_list.item("0", "tags"))
        self.app.undo()
        self.assertEqual(self.rows()[0][3], "원본")                 # 되돌리면 다시 '원본'
        self.app.on_mouse_down(self.at(50, 50)); self.app.on_mouse_drag(self.at(150, 150))
        self.app.on_mouse_up(self.at(150, 150))
        self.assertEqual([r[3] for r in self.rows()], ["원본", "변경"])
        self.assertIn("(2개)", self.app.box_title.cget("text"))

    def test_clicking_a_row_selects_that_box(self):
        self.app.on_mouse_down(self.at(50, 50)); self.app.on_mouse_drag(self.at(150, 150))
        self.app.on_mouse_up(self.at(150, 150))                     # 2번째 BBox 가 선택된 상태
        self.assertEqual(self.app.selected, 1)
        self.assertEqual(self.app.box_list.selection(), ("1",))     # 표에서도 같은 줄이 선택돼 있다
        self.app.box_list.selection_set("0")
        self.root.update()
        self.assertEqual(self.app.selected, 0)                      # 표를 눌러 바꾼 선택이 화면에도 반영
        self.assertEqual(len(self.app.canvas.find_withtag("handle")), 8)

    def test_table_refresh_does_not_trigger_a_selection_loop(self):
        self.app.select_box(0)
        picks = []
        orig = self.app.select_box
        self.app.select_box = lambda i: (picks.append(i), orig(i))[1]
        for _ in range(5):
            self.app.refresh_box_list()
            self.root.update()
        self.assertEqual(picks, [])                                 # 표를 다시 채워도 선택 함수가 되풀이 호출되지 않는다

    def test_empty_table_when_no_boxes(self):
        self.app.boxes.clear(); self.app.selected = None
        self.app.refresh_box_list()
        self.assertEqual(self.rows(), [])
        self.assertIn("(0개)", self.app.box_title.cget("text"))

    # ── 툴바: 이동(Pan) 모드와 배율 표시 ───────────────────────
    def test_pan_mode_drags_the_view_with_the_left_button(self):
        self.app.pan_var.set(True); self.app.on_pan_toggled()
        ox, oy = self.app.vp.offset_x, self.app.vp.offset_y
        self.app.on_mouse_down(Ev(300, 300)); self.app.on_mouse_drag(Ev(340, 320)); self.app.on_mouse_up(Ev(340, 320))
        self.assertEqual((self.app.vp.offset_x - ox, self.app.vp.offset_y - oy), (40, 20))   # 화면이 따라 움직였다
        self.assertEqual(len(self.app.boxes), 1)                                              # BBox 는 만들어지지 않는다
        self.assertEqual(self.box(), (400.0, 240.0, 600.0, 360.0))                           # 기존 BBox 도 안 움직인다
        self.assertFalse(self.app.dirty)
        self.assertIsNone(self.app.pan_last)

    def test_pan_mode_can_be_turned_off_again(self):
        self.app.pan_var.set(True); self.app.on_pan_toggled()
        self.app.pan_var.set(False); self.app.on_pan_toggled()
        self.app.on_mouse_down(self.at(50, 50)); self.app.on_mouse_drag(self.at(150, 150))
        self.app.on_mouse_up(self.at(150, 150))
        self.assertEqual(len(self.app.boxes), 2)                                              # 다시 BBox 를 그린다

    def test_zoom_percent_label_follows_the_scale(self):
        self.assertEqual(self.app.zoom_label.cget("text"), f"{self.app.vp.zoom_percent}%")
        self.app.zoom_in()
        self.assertEqual(self.app.zoom_label.cget("text"), f"{self.app.vp.zoom_percent}%")

    def test_toolbar_has_every_main_action(self):
        def buttons(w):
            out = []
            for c in w.winfo_children():
                if c.winfo_class() in ("Button", "Checkbutton"):
                    out.append(c.cget("text"))
                out += buttons(c)
            return out
        names = " ".join(buttons(self.app.root))
        for label in ("이미지 열기", "폴더 열기", "저장", "저장+다음", "되돌리기", "다시", "삭제", "전체 삭제", "맞춤", "이동 모드",
                      "데이터 조사", "QA 검증", "다시 불러오기", "WORK 폴더"):
            self.assertIn(label, names)

    # ── 저장 후 다음 ──────────────────────────────────────────
    def add_second_photo(self):
        """같은 폴더에 사진 한 장을 더 만들고 목록을 새로 읽는다."""
        folder = self.app.image_path.parent
        Image.new("RGB", (IMG_W, IMG_H), "blue").save(folder / "b.jpg")
        self.app.navigator.set_current(self.app.image_path.parent / "b.jpg")
        self.app.navigator.set_current(folder / "a.jpg")
        self.app.update_nav()

    def test_save_and_next_saves_then_moves(self):
        from src.data_paths import work_label_path
        self.add_second_photo()
        first = self.app.image_path
        self.app.on_mouse_down(self.at(500, 300)); self.app.on_mouse_drag(self.at(560, 300))
        self.app.on_mouse_up(self.at(560, 300))
        self.app.save_and_next()
        self.root.update()
        self.assertTrue(work_label_path(first).is_file())                  # 먼저 저장했고
        self.assertEqual(self.app.image_path.name, "b.jpg")                # 다음 사진으로 넘어왔다
        self.assertFalse(self.app.dirty)

    def test_save_and_next_on_the_last_photo_saves_and_stays(self):
        from src.data_paths import work_label_path
        self.app.save_and_next()
        self.assertTrue(work_label_path(self.app.image_path).is_file())
        self.assertEqual(self.app.image_path.name, "a.jpg")
        self.assertIn("마지막 사진", self.app.status.cget("text"))

    def test_save_and_next_does_not_move_when_saving_fails(self):
        self.add_second_photo()
        self.app.save = lambda: False
        self.app.save_and_next()
        self.assertEqual(self.app.image_path.name, "a.jpg")

    # ── Diff 보기 ─────────────────────────────────────────────
    def canvas_texts(self):
        c = self.app.canvas
        return [c.itemcget(i, "text") for i in c.find_withtag("box") if c.type(i) == "text"]

    def turn_diff_on(self):
        self.app.diff_var.set(True)
        self.app.on_diff_toggled()

    def test_diff_is_off_by_default_and_shows_no_marks(self):
        self.assertFalse(self.app.diff_var.get())
        self.assertFalse(any("[" in t for t in self.canvas_texts()))
        self.assertEqual(self.app.diff_label.cget("text"), "")

    def test_diff_unchanged(self):
        self.turn_diff_on()
        self.assertEqual(self.app.diff_label.cget("text"), "추가 0 · 수정 0 · 삭제 0 · 그대로 1")
        self.assertFalse(any("[" in t for t in self.canvas_texts()))

    def test_diff_shows_modified_with_the_original_position(self):
        self.turn_diff_on()
        self.app.on_mouse_down(self.at(500, 300)); self.app.on_mouse_drag(self.at(540, 310))
        self.app.on_mouse_up(self.at(540, 310))
        self.assertIn("수정 1", self.app.diff_label.cget("text"))
        texts = self.canvas_texts()
        self.assertTrue(any("[수정]" in t for t in texts))
        self.assertTrue(any(t.startswith("원본") for t in texts))          # 원래 위치의 회색 점선

    def test_diff_shows_added_and_deleted(self):
        self.turn_diff_on()
        self.app.on_mouse_down(self.at(50, 50)); self.app.on_mouse_drag(self.at(150, 150))
        self.app.on_mouse_up(self.at(150, 150))                            # 새 BBox
        self.assertTrue(any("[추가]" in t for t in self.canvas_texts()))
        self.app.select_box(0); self.app.delete_selected()                 # 원본 BBox 삭제
        self.assertTrue(any(t.startswith("삭제됨") for t in self.canvas_texts()))
        self.assertIn("추가 1 · 수정 0 · 삭제 1", self.app.diff_label.cget("text"))

    def test_diff_for_a_photo_without_raw_label(self):
        self.app.raw_boxes = []
        self.turn_diff_on()
        self.assertIn("원본 라벨이 없는 사진", self.app.diff_label.cget("text"))

    def test_diff_turned_off_clears_the_marks(self):
        self.turn_diff_on()
        self.app.on_mouse_down(self.at(500, 300)); self.app.on_mouse_drag(self.at(560, 300))
        self.app.on_mouse_up(self.at(560, 300))
        self.app.diff_var.set(False); self.app.on_diff_toggled()
        self.assertFalse(any("[" in t or t.startswith("원본") for t in self.canvas_texts()))
        self.assertEqual(self.app.diff_label.cget("text"), "")

    def test_clear_all_asks_then_can_be_undone(self):
        from src.ui import main_window as mw
        asked = []
        mw.messagebox.askyesno = lambda *a, **k: (asked.append(a[1]), True)[1]
        self.app.on_mouse_down(self.at(50, 50)); self.app.on_mouse_drag(self.at(150, 150))
        self.app.on_mouse_up(self.at(150, 150))                    # BBox 2개로 만든다
        self.assertEqual(len(self.app.boxes), 2)
        self.app.clear_all()
        self.assertEqual(self.app.boxes, [])
        self.assertIsNone(self.app.selected)
        self.assertEqual(len(asked), 1)
        self.assertIn("2개", asked[0])                             # 몇 개를 지우는지 알려 준다
        self.app.undo()
        self.assertEqual(len(self.app.boxes), 2)                   # 한 번에 되돌아온다

    def test_clear_all_can_be_declined(self):
        from src.ui import main_window as mw
        mw.messagebox.askyesno = lambda *a, **k: False
        self.app.clear_all()
        self.assertEqual(len(self.app.boxes), 1)
        self.assertEqual(len(self.app.history), 0)
        self.assertFalse(self.app.dirty)

    def test_clear_all_with_no_boxes_does_not_ask(self):
        from src.ui import main_window as mw
        asked = []
        mw.messagebox.askyesno = lambda *a, **k: (asked.append(1), True)[1]
        self.app.boxes.clear()
        self.app.clear_all()
        self.assertEqual(asked, [])

    def test_click_only_selects(self):
        self.app.on_mouse_down(self.at(500, 300)); self.app.on_mouse_up(self.at(500, 300))
        self.assertEqual(self.app.selected, 0)
        self.assertFalse(self.app.dirty)
        self.assertEqual(len(self.app.history), 0)
        self.assertEqual(self.box(), (400.0, 240.0, 600.0, 360.0))

    def test_drag_inside_moves_the_box(self):
        self.app.on_mouse_down(self.at(500, 300))
        self.app.on_mouse_drag(self.at(550, 330)); self.app.on_mouse_up(self.at(550, 330))
        self.assertEqual(len(self.app.boxes), 1)                  # 새 BBox 가 생기지 않는다
        self.assertEqual(self.box(), (450.0, 270.0, 650.0, 390.0))
        self.assertTrue(self.app.dirty)
        self.assertEqual(len(self.app.history), 1)

    def test_move_can_be_undone_and_redone(self):
        self.app.on_mouse_down(self.at(500, 300))
        self.app.on_mouse_drag(self.at(600, 300)); self.app.on_mouse_up(self.at(600, 300))
        self.assertEqual(self.box(), (500.0, 240.0, 700.0, 360.0))
        self.app.undo()
        self.assertEqual(self.box(), (400.0, 240.0, 600.0, 360.0))
        self.assertFalse(self.app.dirty)                          # 처음 상태까지 되돌렸다
        self.app.redo()
        self.assertEqual(self.box(), (500.0, 240.0, 700.0, 360.0))

    def test_move_stops_at_the_image_edge(self):
        self.app.on_mouse_down(self.at(500, 300))
        self.app.on_mouse_drag(self.at(990, 590)); self.app.on_mouse_up(self.at(990, 590))     # 이미지 오른쪽 아래 끝까지
        x1, y1, x2, y2 = self.box()
        self.assertLessEqual(x2, IMG_W)
        self.assertLessEqual(y2, IMG_H)
        self.assertEqual((x2 - x1, y2 - y1), (200.0, 120.0))      # 크기는 그대로

    def test_resize_with_a_handle(self):
        self.app.select_box(0)
        self.app.on_mouse_down(self.at(600, 360))                 # 오른쪽 아래(se) 핸들
        self.assertEqual(self.app.drag["mode"], "resize")
        self.app.on_mouse_drag(self.at(700, 450)); self.app.on_mouse_up(self.at(700, 450))
        self.assertEqual(self.box(), (400.0, 240.0, 700.0, 450.0))
        self.assertEqual(len(self.app.history), 1)
        self.app.undo()
        self.assertEqual(self.box(), (400.0, 240.0, 600.0, 360.0))

    def test_handle_is_ignored_when_nothing_is_selected(self):
        self.app.on_mouse_down(self.at(603, 363))                 # 선택 안 한 BBox 의 핸들 자리 = 빈 곳
        self.assertEqual(self.app.drag["mode"], "new")
        self.app.cancel_drag()

    def test_drag_in_empty_area_still_creates_a_box(self):
        self.app.on_mouse_down(self.at(50, 50))
        self.app.on_mouse_drag(self.at(150, 120)); self.app.on_mouse_up(self.at(150, 120))
        self.assertEqual(len(self.app.boxes), 2)
        self.assertEqual(self.box(0), (400.0, 240.0, 600.0, 360.0))   # 기존 BBox 는 그대로

    def test_shift_drag_over_a_box_creates_a_new_box(self):
        self.app.on_mouse_down(self.at(450, 270, state=1))
        self.assertEqual(self.app.drag["mode"], "new")
        self.app.on_mouse_drag(self.at(520, 330, state=1)); self.app.on_mouse_up(self.at(520, 330, state=1))
        self.assertEqual(len(self.app.boxes), 2)
        self.assertEqual(self.box(0), (400.0, 240.0, 600.0, 360.0))

    def test_escape_cancels_a_move(self):
        self.app.on_mouse_down(self.at(500, 300))
        self.app.on_mouse_drag(self.at(600, 400))
        self.assertNotEqual(self.box(), (400.0, 240.0, 600.0, 360.0))
        self.app.on_escape()
        self.assertEqual(self.box(), (400.0, 240.0, 600.0, 360.0))
        self.app.on_mouse_up(self.at(600, 400))                   # 뒤늦게 버튼을 떼도 아무 일 없다
        self.assertEqual(len(self.app.history), 0)
        self.assertFalse(self.app.dirty)

    def test_escape_cancels_a_new_box_and_then_clears_selection(self):
        self.app.on_mouse_down(self.at(50, 50)); self.app.on_mouse_drag(self.at(150, 150))
        self.app.on_escape()
        self.app.on_mouse_up(self.at(150, 150))
        self.assertEqual(len(self.app.boxes), 1)
        self.app.select_box(0)
        self.app.on_escape()                                      # 드래그 중이 아니면 선택 해제
        self.assertIsNone(self.app.selected)

    def test_tiny_wobble_is_not_a_move(self):
        self.app.on_mouse_down(self.at(500, 300))
        self.app.on_mouse_drag(Ev(self.at(500, 300).x + 2, self.at(500, 300).y + 1))
        self.app.on_mouse_up(self.at(500, 300))
        self.assertEqual(len(self.app.history), 0)
        self.assertFalse(self.app.dirty)

    def test_undo_is_ignored_while_dragging(self):
        self.app.on_mouse_down(self.at(500, 300)); self.app.on_mouse_drag(self.at(560, 300))
        self.assertFalse(self.app.undo())
        self.assertFalse(self.app.redo())
        self.app.on_mouse_up(self.at(560, 300))

    def test_saved_file_has_the_moved_position(self):
        self.app.on_mouse_down(self.at(500, 300))
        self.app.on_mouse_drag(self.at(600, 300)); self.app.on_mouse_up(self.at(600, 300))
        self.assertTrue(self.app.save())
        from src.data_paths import work_label_path
        parts = work_label_path(self.app.image_path).read_text().split()
        self.assertEqual(parts[0], "2")
        self.assertAlmostEqual(float(parts[1]), 0.6, places=6)    # x 중심 0.5 → 0.6
        self.assertAlmostEqual(float(parts[2]), 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
