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
