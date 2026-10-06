"""폴더 끌어다 놓기 도우미 시험 — 화면 없이 경로 변환·대상 고르기만 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_folder_drop.py
"""
import tempfile
import unittest
from pathlib import Path

from src.ui.folder_drop import pick_target, to_local_path


class ToLocalPathTest(unittest.TestCase):
    def test_plain_path_is_unchanged(self):
        self.assertEqual(to_local_path("/home/user/data"), "/home/user/data")

    def test_file_uri_is_decoded(self):
        self.assertEqual(to_local_path("file:///home/user/my%20data"), "/home/user/my data")

    def test_spaces_around_are_removed(self):
        self.assertEqual(to_local_path("  /home/user/data \n"), "/home/user/data")


class PickTargetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "folder").mkdir()
        (self.tmp / "a.jpg").write_bytes(b"x")
        (self.tmp / "b.txt").write_text("x")

    def test_folder_is_preferred(self):
        kind, path = pick_target([str(self.tmp / "a.jpg"), str(self.tmp / "folder")])
        self.assertEqual((kind, path.name), ("folder", "folder"))

    def test_jpg_when_no_folder(self):
        kind, path = pick_target([str(self.tmp / "b.txt"), str(self.tmp / "a.jpg")])
        self.assertEqual((kind, path.name), ("image", "a.jpg"))

    def test_nothing_usable(self):
        self.assertIsNone(pick_target([str(self.tmp / "b.txt"), str(self.tmp / "missing.jpg"), ""]))
        self.assertIsNone(pick_target([]))


if __name__ == "__main__":
    unittest.main()
