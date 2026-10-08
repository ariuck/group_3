"""라벨 파일 읽기 시험 (BOM·형식이 다른 줄·읽지 못한 줄 경고).

실행 (프로젝트 폴더에서):  python -m unittest tests/test_label_io.py
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src import settings
from src.validation.validator import parse_label_file
from src.yolo.yolo_loader import label_signature, parse_class_id, read_yolo_file, read_yolo_rows


class LabelReadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, text, name="a.txt"):
        p = self.tmp / name
        p.write_bytes(text.encode("utf-8"))
        return p

    def test_bom_is_ignored(self):
        """(수정한 버그) Windows 메모장·엑셀이 붙이는 BOM 때문에 첫 줄이 통째로 읽히지 않던 문제"""
        f = self.write("\ufeff2 0.5 0.5 0.2 0.2\n0 0.1 0.1 0.1 0.1\n")
        boxes, bad = read_yolo_file(f, 1000, 800)
        self.assertEqual((len(boxes), bad), (2, 0))
        self.assertEqual(boxes[0]["cls"], 2)
        self.assertEqual(len(read_yolo_rows(f)), 2)
        self.assertEqual(len(label_signature(f)), 2)
        rows, errors = parse_label_file(f)
        self.assertEqual((len(rows), len(errors)), (2, []) if False else (2, len(errors)))
        self.assertEqual(errors, [])

    def test_class_written_as_a_float_is_accepted_when_it_is_a_whole_number(self):
        self.assertEqual(parse_class_id("2"), 2)
        self.assertEqual(parse_class_id("2.0"), 2)
        with self.assertRaises(ValueError):
            parse_class_id("2.5")
        with self.assertRaises(ValueError):
            parse_class_id("abc")
        boxes, bad = read_yolo_file(self.write("2.0 0.5 0.5 0.2 0.2\n"), 1000, 800)
        self.assertEqual((len(boxes), bad, boxes[0]["cls"]), (1, 0, 2))

    def test_line_endings_and_blank_lines(self):
        boxes, bad = read_yolo_file(self.write("2 0.5 0.5 0.2 0.2\r\n\r\n  0 0.1 0.1 0.1 0.1  \r\n"), 1000, 800)
        self.assertEqual((len(boxes), bad), (2, 0))

    def test_unreadable_lines_are_counted_not_hidden(self):
        f = self.write("2 0.5 0.5 0.2 0.2\ngarbage\n2,0.5,0.5,0.2,0.2\n2 0.5 0.5 0.2 0.2 0.93\n2 0.5 0.5\n")
        boxes, bad = read_yolo_file(f, 1000, 800)
        self.assertEqual((len(boxes), bad), (1, 4))                  # 쉼표 구분·6칸·3칸·글자 줄은 읽지 못한 줄

    def test_empty_file_is_not_an_error(self):
        self.assertEqual(read_yolo_file(self.write(""), 1000, 800), ([], 0))


class UnreadableLinesUiTest(unittest.TestCase):
    def setUp(self):
        from src.ui import main_window as mw
        self.mw = mw
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        ds = self.tmp / "raw" / "DS1"
        (ds / "images" / "train").mkdir(parents=True)
        (ds / "labels" / "train").mkdir(parents=True)
        Image.new("RGB", (800, 600), "green").save(ds / "images" / "train" / "a.jpg")
        (ds / "labels" / "train" / "a.txt").write_text("2 0.5 0.5 0.2 0.2\ngarbage line\n0,0.1,0.1,0.1,0.1\n")
        settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = self.tmp / "raw", self.tmp / "work", self.tmp / "m.csv"
        self.asked = []
        mw.messagebox.showwarning = mw.messagebox.showerror = mw.messagebox.showinfo = lambda *a, **k: None
        mw.messagebox.askyesnocancel = lambda *a, **k: False
        try:
            self.root = mw.make_root()
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.app = mw.Day1Labeler(self.root)
        self.root.geometry("1300x850")
        self.root.update()
        self.app.load_image(str(ds / "images" / "train" / "a.jpg"))
        self.root.update()
        self.work = settings.WORK_DIR / "DS1" / "labels" / "train" / "a.txt"

    def tearDown(self):
        self.app.shutdown()
        self.root.destroy()

    def answer(self, value):
        self.mw.messagebox.askyesno = lambda *a, **k: (self.asked.append(a[0]), value)[1]

    def test_warning_stays_visible_above_the_image(self):
        self.assertIn("읽지 못한 줄 2개", self.app.warn_label.cget("text"))
        self.app.on_mouse_move(type("E", (), {"x": 50, "y": 50, "state": 0})())     # 마우스를 움직여도 사라지지 않는다
        self.assertIn("읽지 못한 줄 2개", self.app.warn_label.cget("text"))

    def test_save_asks_first_and_declining_writes_nothing(self):
        self.answer(False)
        self.assertFalse(self.app.save())
        self.assertEqual(len(self.asked), 1)
        self.assertFalse(self.work.exists())                          # 거절하면 파일을 만들지 않는다

    def test_confirming_saves_only_the_readable_line_and_asks_once(self):
        self.answer(True)
        self.assertTrue(self.app.save())
        self.assertEqual(self.work.read_text().strip().splitlines(), ["2 0.5000000000 0.5000000000 0.2000000000 0.2000000000"])
        self.assertEqual(self.app.warn_label.cget("text"), "")        # 저장한 뒤에는 경고가 사라진다
        self.app.dirty = True
        self.assertTrue(self.app.save())
        self.assertEqual(len(self.asked), 1)                          # 두 번째 저장에서는 다시 묻지 않는다

    def test_original_label_is_never_changed(self):
        raw = settings.RAW_DIR / "DS1" / "labels" / "train" / "a.txt"
        before = raw.read_bytes()
        self.answer(True)
        self.app.save()
        self.assertEqual(raw.read_bytes(), before)

    def test_a_clean_photo_does_not_ask(self):
        self.answer(True)
        self.app.unreadable = 0
        self.assertTrue(self.app.save())
        self.assertEqual(self.asked, [])


if __name__ == "__main__":
    unittest.main()
