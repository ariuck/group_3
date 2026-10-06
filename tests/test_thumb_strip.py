"""하단 사진 목록(썸네일 줄)과 검수표 상태 읽기 시험.

화면(Tk)이 필요하다.  실행 (프로젝트 폴더에서):  python -m unittest tests/test_thumb_strip.py
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src import settings
from src.manifest import manifest_writer as mw


def make_photos(count, size=(640, 480)):
    tmp = Path(tempfile.mkdtemp())
    files = []
    for i in range(count):
        p = tmp / f"img{i:03d}.jpg"
        Image.new("RGB", size, (i * 8 % 255, 100, 150)).save(p)
        files.append(p)
    return tmp, files


class StatusMapTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.old = (settings.RAW_DIR, settings.MANIFEST_PATH)
        settings.RAW_DIR, settings.MANIFEST_PATH = self.tmp / "raw", self.tmp / "m.csv"
        self.addCleanup(lambda: setattr(settings, "RAW_DIR", self.old[0]))
        self.addCleanup(lambda: setattr(settings, "MANIFEST_PATH", self.old[1]))

    def row(self, name, status, dataset="DS1", split="train"):
        r = {h: "" for h in mw.HEADERS}
        r.update({"이미지 파일명": name, "상태": status, "출처 데이터셋": dataset, "원래 split": split})
        return r

    def test_no_file_gives_empty_map(self):
        self.assertEqual(mw.read_status_map(), {})

    def test_map_and_lookup(self):
        mw._save(settings.MANIFEST_PATH, [self.row("a.jpg", "수정 완료"), self.row("b.jpg", "검수 완료", split="validation")])
        m = mw.read_status_map()
        self.assertEqual(m[("DS1", "train", "a.jpg")], "수정 완료")
        img = settings.RAW_DIR / "DS1" / "images" / "train" / "a.jpg"
        self.assertEqual(mw.status_of(img, m), "수정 완료")
        img_val = settings.RAW_DIR / "DS1" / "images" / "validation" / "b.jpg"
        self.assertEqual(mw.status_of(img_val, m), "검수 완료")

    def test_unknown_or_outside_raw_is_blank(self):
        mw._save(settings.MANIFEST_PATH, [self.row("a.jpg", "수정 완료")])
        m = mw.read_status_map()
        self.assertEqual(mw.status_of(settings.RAW_DIR / "DS1" / "images" / "train" / "zzz.jpg", m), "")
        self.assertEqual(mw.status_of(self.tmp / "other" / "a.jpg", m), "")      # RAW 밖


class ThumbStripTest(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from src.ui.thumb_strip import ThumbStrip
        try:
            self.root = tk.Tk()
        except tk.TclError as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.root.geometry("1100x300")
        self.tmp, self.files = make_photos(40)
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.selected = []
        self.marks = {}
        self.strip = ThumbStrip(self.root, on_select=self.selected.append,
                                mark_of=lambda p: self.marks.get(p.name, ("", "#333333")))
        self.strip.pack(fill="x")
        self.root.update()

    def tearDown(self):
        self.strip.stop()
        self.root.destroy()

    def settle(self):
        """보이는 미리보기를 모두 읽을 때까지 기다린다."""
        for _ in range(400):
            self.root.update()
            if not self.strip._queue and self.strip._job is None:
                break

    def test_visible_count_follows_the_width(self):
        self.strip.set_files(self.files)
        self.strip._fit_count()
        self.root.update()
        wide = self.strip._visible
        self.assertGreaterEqual(wide, 5)
        self.root.geometry("560x300")
        self.root.update()
        self.strip._fit_count()
        self.assertLess(self.strip._visible, wide)                      # 좁아지면 적게 보인다

    def test_title_shows_the_count(self):
        self.strip.set_files(self.files)
        self.assertIn("40개", self.strip.title.cget("text"))

    def test_current_photo_is_scrolled_into_view_and_highlighted(self):
        self.strip.set_files(self.files)
        self.strip.set_current(30)
        lo, hi = self.strip.visible_range
        self.assertTrue(lo <= 30 < hi)
        cur = [c for c in self.strip.cells if c.index == 30][0]
        self.assertEqual(cur.frame.cget("bg"), "#1e88e5")                # 파란 테두리
        others = [c for c in self.strip.cells if c.index not in (None, 30)]
        self.assertTrue(all(c.frame.cget("bg") != "#1e88e5" for c in others))

    def test_moving_inside_the_window_does_not_scroll(self):
        self.strip.set_files(self.files)
        self.strip.set_current(2)
        start = self.strip.start
        self.strip.set_current(3)
        self.assertEqual(self.strip.start, start)

    def test_click_reports_the_photo_number(self):
        self.strip.set_files(self.files)
        self.strip.set_current(0)
        self.root.update()                                               # 칸이 화면에 배치된 뒤에야 클릭이 닿는다
        cell = [c for c in self.strip.cells if c.index == 2][0]
        for w in (cell.frame, cell.pic, cell.cap):                       # 사진·글자·테두리 어디를 눌러도 이동
            self.assertTrue(w.bind("<Button-1>"))
        cell.pic.event_generate("<Button-1>", x=5, y=5)
        self.root.update()
        self.assertEqual(self.selected, [2])

    def test_thumbnails_load_lazily_and_are_remembered(self):
        self.strip.set_files(self.files)
        self.assertGreater(len(self.strip._queue), 0)                    # 처음에는 회색 상자
        self.settle()
        lo, hi = self.strip.visible_range
        self.assertTrue(all(self.files[i] in self.strip._cache for i in range(lo, hi)))
        loaded = len(self.strip._cache)
        self.strip.set_current(0)
        self.strip.set_files(self.files)                                  # 같은 목록을 다시 넣어도
        self.settle()
        self.assertEqual(len(self.strip._cache), loaded)                  # 다시 읽지 않는다

    def test_nearest_to_current_loads_first(self):
        self.strip.set_files(self.files)
        self.strip.set_current(0)
        self.strip._queue.sort(key=lambda c: abs(c.index - 0))
        self.assertEqual([c.index for c in self.strip._queue][:2], sorted(c.index for c in self.strip._queue)[:2])

    def test_marks_are_shown_under_the_photo(self):
        self.marks["img001.jpg"] = ("✓ 수정 완료", "#e65100")
        self.strip.set_files(self.files)
        cell = [c for c in self.strip.cells if c.index == 1][0]
        self.assertIn("✓ 수정 완료", cell.cap.cget("text"))
        self.assertIn("img001", cell.cap.cget("text"))
        self.marks["img001.jpg"] = ("✓ 검수 완료", "#2e7d32")
        self.strip.refresh_marks()
        self.assertIn("✓ 검수 완료", cell.cap.cget("text"))

    def test_page_buttons_move_by_one_screen(self):
        self.strip.set_files(self.files)
        n = self.strip._visible
        self.strip.page(+1)
        self.assertEqual(self.strip.start, n)
        self.strip.page(-1)
        self.assertEqual(self.strip.start, 0)
        self.strip.page(-1)
        self.assertEqual(self.strip.start, 0)                              # 처음에서 더 못 간다
        for _ in range(20):
            self.strip.page(+1)
        self.assertEqual(self.strip.start, len(self.files) - n)            # 끝에서 더 못 간다

    def test_broken_photo_does_not_break_the_strip(self):
        bad = self.tmp / "broken.jpg"
        bad.write_bytes(b"not a jpeg")
        self.strip.set_files([bad] + self.files[:3])
        self.settle()
        self.assertIn(bad, self.strip._cache)                             # 회색 상자로 대신한다

    def test_empty_list(self):
        self.strip.set_files([])
        self.strip.set_current(-1)
        self.assertEqual(self.strip.visible_range, (0, 0))


if __name__ == "__main__":
    unittest.main()
