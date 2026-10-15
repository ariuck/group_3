"""이상한 BBox(이미지 밖·Class 범위 밖 등) 찾기와 화면 표시 시험.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_box_problems.py
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src import settings
from src.bbox.bbox_manager import box_problems

W, H = 1000, 800


def B(cls, x1, y1, x2, y2):
    return {"cls": cls, "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}


class BoxProblemsTest(unittest.TestCase):
    def test_normal_box_has_no_problem(self):
        self.assertEqual(box_problems(B(2, 100, 100, 300, 300), W, H), [])
        self.assertEqual(box_problems(B(6, 0, 0, W, H), W, H), [])             # 이미지 전체도 정상

    def test_class_out_of_range(self):
        out = box_problems(B(9, 100, 100, 300, 300), W, H)
        self.assertEqual(len(out), 1)
        self.assertIn("범위 밖", out[0])
        self.assertTrue(box_problems(B(-1, 100, 100, 300, 300), W, H))

    def test_unused_class(self):
        out = box_problems(B(4, 100, 100, 300, 300), W, H, unused={4})
        self.assertEqual(len(out), 1)
        self.assertIn("사용하지 않는", out[0])
        self.assertEqual(box_problems(B(4, 100, 100, 300, 300), W, H), [])      # 사용 안 하는 번호를 모르면 검사하지 않는다

    def test_outside_the_image(self):
        for box in (B(2, -50, 100, 300, 300), B(2, 100, -5, 300, 300), B(2, 100, 100, W + 20, 300), B(2, 100, 100, 300, H + 1)):
            self.assertIn("이미지 밖으로 나감", box_problems(box, W, H))
        self.assertEqual(box_problems(B(2, -0.4, 0, 300, H + 0.4), W, H), [])   # 반올림 오차 정도는 정상

    def test_too_small(self):
        self.assertTrue(any("너무 작음" in p for p in box_problems(B(2, 100, 100, 102, 300), W, H)))

    def test_several_problems_are_all_reported(self):
        self.assertEqual(len(box_problems(B(9, -10, 0, 2, 3), W, H)), 3)


class ProblemBoxUiTest(unittest.TestCase):
    def setUp(self):
        from src.ui import main_window as mw
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        ds = self.tmp / "raw" / "DS1"
        (ds / "images" / "train").mkdir(parents=True)
        (ds / "labels" / "train").mkdir(parents=True)
        Image.new("RGB", (W, H), "green").save(ds / "images" / "train" / "a.jpg")
        # 정상 1개 + Class 9 + 이미지보다 훨씬 큰 BBox
        (ds / "labels" / "train" / "a.txt").write_text("2 0.5 0.5 0.2 0.2\n9 0.5 0.5 0.1 0.1\n1 0.5 0.5 3 3\n")
        settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = self.tmp / "raw", self.tmp / "work", self.tmp / "m.csv"
        mw.messagebox.showwarning = mw.messagebox.showerror = mw.messagebox.showinfo = lambda *a, **k: None
        try:
            self.root = mw.make_root()
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.app = mw.Day1Labeler(self.root)
        self.root.geometry("1300x850")
        self.root.update()
        self.app.load_image(str(ds / "images" / "train" / "a.jpg"))
        self.root.update()

    def tearDown(self):
        self.app.shutdown()
        self.root.destroy()

    def rows(self):
        return [self.app.box_list.item(i, "values") for i in self.app.box_list.get_children()]

    def test_load_message_counts_the_odd_boxes(self):
        self.assertIn("확인이 필요한 BBox 2개", self.app.status.cget("text"))

    def test_table_marks_only_the_odd_ones(self):
        self.assertEqual([r[3] for r in self.rows()], ["원본", "⚠ 확인", "⚠ 확인"])
        self.assertIn("problem", self.app.box_list.item("1", "tags"))
        self.assertNotIn("problem", self.app.box_list.item("0", "tags"))

    def test_selected_odd_box_explains_why_in_the_coordinate_bar(self):
        self.app.select_box(1)
        text = self.app.bbox_info.cget("text")
        self.assertIn("⚠", text)
        self.assertIn("범위 밖", text)
        self.app.select_box(0)
        self.assertNotIn("⚠", self.app.bbox_info.cget("text"))

    def test_odd_boxes_are_drawn_with_a_warning_label(self):
        c = self.app.canvas
        texts = [c.itemcget(i, "text") for i in c.find_withtag("box") if c.type(i) == "text"]
        self.assertEqual(sum(1 for t in texts if t.startswith("⚠")), 2)

    def test_the_odd_boxes_are_kept_not_silently_fixed(self):
        self.assertEqual(len(self.app.boxes), 3)                              # 자동으로 고치거나 지우지 않는다
        self.assertEqual(self.app.boxes[1]["cls"], 9)

    def test_fixing_the_class_removes_the_warning(self):
        self.app.select_box(1)
        self.app.choose_class(3)
        self.assertEqual(self.rows()[1][3], "변경")
        self.assertEqual(self.app.boxes[1]["cls"], 3)


if __name__ == "__main__":
    unittest.main()
