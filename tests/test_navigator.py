"""② 이동(navigator) 시험 — 화면 없이 사진 목록·이전/다음·진행률만 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_navigator.py
"""
import atexit
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ui.navigator import ImageNavigator


def make_folder(names):
    base = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, base, True)             # 시험이 끝나면 임시 폴더를 지운다
    folder = base / "images" / "train"
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

    def test_load_folder(self):
        folder = make_folder(["img1.jpg", "img2.jpg", "img3.jpg"])
        nav = ImageNavigator()
        first = nav.load_folder(folder.parents[1])
        self.assertEqual(first.name, "img1.jpg")
        self.assertEqual(nav.total, 3)
        self.assertEqual(nav.progress_text(), "1 / 3")
        self.assertEqual(nav.next_path().name, "img2.jpg")


class JumpToIndexTest(unittest.TestCase):
    def test_jump_to_index(self):
        folder = make_folder(["img1.jpg", "img2.jpg", "img3.jpg"])
        nav = ImageNavigator()
        nav.load_folder(folder)
        self.assertEqual(nav.jump_to_index(0).name, "img1.jpg")
        self.assertEqual(nav.jump_to_index(2).name, "img3.jpg")
        self.assertIsNone(nav.jump_to_index(-1))
        self.assertIsNone(nav.jump_to_index(3))


class LoadFolderTest(unittest.TestCase):
    def test_folder_with_photos_directly(self):
        folder = make_folder(["b.jpg", "a.jpg", "note.txt"])
        nav = ImageNavigator()
        self.assertEqual(nav.load_folder(folder).name, "a.jpg")
        self.assertEqual([p.name for p in nav.files], ["a.jpg", "b.jpg"])
        self.assertEqual(nav.progress_text(), "1 / 2")

    def test_dataset_folder_finds_photos_in_subfolders(self):
        base = Path(tempfile.mkdtemp())
        atexit.register(shutil.rmtree, base, True)
        root = base / "DS1"
        for split, names in (("train", ["a.jpg", "b.jpg"]), ("val", ["c.jpg"])):
            (root / "images" / split).mkdir(parents=True)
            for n in names:
                (root / "images" / split / n).write_bytes(b"x")
        nav = ImageNavigator()
        nav.load_folder(root)
        self.assertEqual(nav.total, 3)
        self.assertEqual([p.name for p in nav.files], ["a.jpg", "b.jpg", "c.jpg"])   # train 다음 val

    def test_split_folders_are_grouped_not_mixed_by_name(self):
        base = Path(tempfile.mkdtemp())
        atexit.register(shutil.rmtree, base, True)
        root = base / "DS1"
        for split, names in (("train", ["b.jpg", "d.jpg"]), ("val", ["a.jpg", "c.jpg"])):
            (root / "images" / split).mkdir(parents=True)
            for n in names:
                (root / "images" / split / n).write_bytes(b"x")
        nav = ImageNavigator()
        nav.load_folder(root)
        self.assertEqual([p.name for p in nav.files], ["b.jpg", "d.jpg", "a.jpg", "c.jpg"])   # val 이 train 사이에 섞이지 않는다

    def test_empty_folder_returns_none_and_keeps_current_list(self):
        nav = ImageNavigator()
        nav.load_folder(make_folder(["a.jpg", "b.jpg"]))
        self.assertIsNone(nav.load_folder(make_folder(["x.txt"])))
        self.assertEqual(nav.total, 2)                       # 사진이 없는 폴더는 지금 목록을 바꾸지 않는다

    def test_list_is_kept_when_photo_inside_is_opened(self):
        base = Path(tempfile.mkdtemp())
        atexit.register(shutil.rmtree, base, True)
        root = base / "DS1"
        for split in ("train", "val"):
            (root / "images" / split).mkdir(parents=True)
            (root / "images" / split / f"{split}1.jpg").write_bytes(b"x")
        nav = ImageNavigator()
        nav.set_current(nav.load_folder(root))
        self.assertEqual(nav.progress_text(), "1 / 2")       # train 폴더만이 아니라 폴더 전체가 목록
        self.assertEqual(nav.next_path().name, "val1.jpg")

    def test_opening_a_photo_outside_the_folder_rebuilds_its_own_list(self):
        f1 = make_folder(["a.jpg", "b.jpg"])
        f2 = make_folder(["x.jpg", "y.jpg", "z.jpg"])
        nav = ImageNavigator()
        nav.load_folder(f1)
        nav.set_current(f2 / "y.jpg")
        self.assertEqual(nav.progress_text(), "2 / 3")


if __name__ == "__main__":
    unittest.main()
