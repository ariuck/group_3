"""② 이동(navigator) 시험 — 화면 없이 사진 목록·이전/다음·진행률만 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_navigator.py
"""
import tempfile
import unittest
from pathlib import Path

from src.ui.navigator import ImageNavigator


def make_folder(names):
    folder = Path(tempfile.mkdtemp()) / "images" / "train"
    folder.mkdir(parents=True)
    for n in names:
        (folder / n).write_bytes(b"x")          # 내용은 필요 없다 (목록만 본다)
    return folder


class NavigatorTest(unittest.TestCase):
    def test_natural_order(self):
        folder = make_folder(["img10.jpg", "img2.jpg", "img1.jpg"])
        nav = ImageNavigator()
        nav.set_current(folder / "img1.jpg")
        self.assertEqual([p.name for p in nav.files], ["img1.jpg", "img2.jpg", "img10.jpg"])

    def test_only_jpg_are_listed(self):
        folder = make_folder(["a.jpg", "b.JPEG", "c.txt", "d.png"])
        nav = ImageNavigator()
        nav.set_current(folder / "a.jpg")
        self.assertEqual(sorted(p.name for p in nav.files), ["a.jpg", "b.JPEG"])

    def test_prev_next_and_progress(self):
        folder = make_folder(["a.jpg", "b.jpg", "c.jpg"])
        nav = ImageNavigator()
        nav.set_current(folder / "a.jpg")
        self.assertEqual(nav.progress_text(), "1 / 3")
        self.assertFalse(nav.has_prev())
        self.assertIsNone(nav.prev_path())
        self.assertEqual(nav.next_path().name, "b.jpg")
        nav.set_current(folder / "c.jpg")
        self.assertEqual(nav.progress_text(), "3 / 3")
        self.assertFalse(nav.has_next())
        self.assertIsNone(nav.next_path())
        self.assertEqual(nav.prev_path().name, "b.jpg")

    def test_nothing_opened_yet(self):
        nav = ImageNavigator()
        self.assertEqual(nav.progress_text(), "0 / 0")
        self.assertFalse(nav.has_prev())
        self.assertFalse(nav.has_next())

    def test_folder_change_rebuilds_list(self):
        f1 = make_folder(["a.jpg", "b.jpg"])
        f2 = make_folder(["x.jpg"])
        nav = ImageNavigator()
        nav.set_current(f1 / "b.jpg")
        nav.set_current(f2 / "x.jpg")
        self.assertEqual(nav.progress_text(), "1 / 1")
        self.assertFalse(nav.has_next())

    def test_file_not_in_list_is_treated_as_single(self):
        folder = make_folder(["a.jpg"])
        nav = ImageNavigator()
        nav.set_current(folder / "a.jpg")
        ghost = folder / "ghost.png"                # 목록에 없는 확장자
        nav.set_current(ghost)
        self.assertEqual(nav.progress_text(), "1 / 1")


if __name__ == "__main__":
    unittest.main()
