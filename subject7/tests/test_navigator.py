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


class FilterTest(unittest.TestCase):
    def setUp(self):
        self.folder = make_folder([f"p{i}.jpg" for i in range(10)])
        self.nav = ImageNavigator()
        self.nav.set_current(self.folder / "p4.jpg")

    def names(self):
        return [p.name for p in self.nav.files]

    def test_filter_keeps_only_matching_photos(self):
        n = self.nav.set_filter(lambda p: int(p.stem[1:]) % 2 == 0)
        self.assertEqual(n, 5)
        self.assertEqual(self.names(), ["p0.jpg", "p2.jpg", "p4.jpg", "p6.jpg", "p8.jpg"])
        self.assertEqual(len(self.nav.all_files), 10)                 # 전체 목록은 그대로
        self.assertTrue(self.nav.filtered)

    def test_current_position_is_kept_when_it_matches(self):
        self.nav.set_filter(lambda p: int(p.stem[1:]) % 2 == 0)
        self.assertEqual(self.nav.index, 2)                           # p4 는 보이는 목록의 3번째
        self.assertEqual(self.nav.progress_text(), "3 / 5")
        self.assertEqual(self.nav.next_path().name, "p6.jpg")         # 이전/다음은 보이는 목록 기준
        self.assertEqual(self.nav.prev_path().name, "p2.jpg")

    def test_index_is_minus_one_when_current_is_filtered_out(self):
        self.nav.set_filter(lambda p: int(p.stem[1:]) % 2 == 1)       # p4 는 짝수라 걸러짐
        self.assertEqual(self.nav.index, -1)
        self.assertEqual(self.nav.progress_text(), "0 / 0")
        self.assertEqual(self.nav.total, 5)

    def test_clearing_the_filter_restores_everything(self):
        self.nav.set_filter(lambda p: False)
        self.assertEqual(self.nav.total, 0)
        self.nav.set_filter(None)
        self.assertEqual(self.nav.total, 10)
        self.assertEqual(self.nav.index, 4)                           # 원래 보던 사진 위치로
        self.assertFalse(self.nav.filtered)

    def test_opening_a_hidden_photo_drops_the_filter(self):
        self.nav.set_filter(lambda p: int(p.stem[1:]) % 2 == 0)
        self.nav.set_current(self.folder / "p5.jpg")                  # 필터에 걸러진 사진을 직접 열었다
        self.assertFalse(self.nav.filtered)
        self.assertEqual(self.nav.total, 10)
        self.assertEqual(self.nav.index, 5)

    def test_new_folder_resets_the_filter(self):
        self.nav.set_filter(lambda p: False)
        other = make_folder(["x.jpg", "y.jpg"])
        self.nav.load_folder(other)
        self.assertFalse(self.nav.filtered)
        self.assertEqual(self.nav.total, 2)

    def test_jump_uses_the_visible_list(self):
        self.nav.set_filter(lambda p: int(p.stem[1:]) >= 7)
        self.assertEqual(self.nav.jump_to_index(0).name, "p7.jpg")
        self.assertIsNone(self.nav.jump_to_index(3))


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
