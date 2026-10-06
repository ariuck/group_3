"""RAW/WORK 경로 처리 시험 (화면 없이).

실행 (프로젝트 폴더에서):  python -m unittest tests/test_data_paths.py
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src import settings
from src.data_paths import find_raw_image, is_inside, locate_in_raw, work_label_path


class DataPathsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.old = (settings.RAW_DIR, settings.WORK_DIR)
        settings.RAW_DIR, settings.WORK_DIR = self.tmp / "raw", self.tmp / "work"
        self.addCleanup(lambda: (setattr(settings, "RAW_DIR", self.old[0]), setattr(settings, "WORK_DIR", self.old[1])))
        for ds, split, name in (("DS1", "train", "same.jpg"), ("DS2", "validation", "same.jpg"), ("DS2", "train", "UPPER.JPG"),
                                ("DS2", "train", "other.jpeg")):
            d = settings.RAW_DIR / ds / "images" / split
            d.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (10, 10)).save(d / name)

    def rel(self, p):
        return str(p.relative_to(settings.RAW_DIR)).replace("\\", "/")

    def test_find_by_full_path_not_by_name_only(self):
        """(수정한 버그) 다른 데이터셋·split 에 같은 이름이 있어도 요청한 곳의 사진을 연다"""
        self.assertEqual(self.rel(find_raw_image("DS2/validation/same")), "DS2/images/validation/same.jpg")
        self.assertEqual(self.rel(find_raw_image("DS1/train/same")), "DS1/images/train/same.jpg")

    def test_uppercase_and_jpeg_extensions(self):
        """(수정한 버그) 대문자 확장자(.JPG)와 .jpeg 도 찾는다"""
        self.assertEqual(self.rel(find_raw_image("DS2/train/UPPER")), "DS2/images/train/UPPER.JPG")
        self.assertEqual(self.rel(find_raw_image("DS2/train/other")), "DS2/images/train/other.jpeg")

    def test_missing_returns_none(self):
        for rel in ("DS2/train/nope", "DS9/train/same", "DS1/validation/same", "same", "", "DS1/"):
            self.assertIsNone(find_raw_image(rel), rel)

    def test_windows_style_separators(self):
        self.assertEqual(self.rel(find_raw_image("DS2\\validation\\same")), "DS2/images/validation/same.jpg")

    def test_locate_and_work_path_keep_the_same_structure(self):
        img = settings.RAW_DIR / "DS2" / "images" / "validation" / "same.jpg"
        self.assertEqual(locate_in_raw(img), ("DS2", "validation"))
        self.assertEqual(work_label_path(img), settings.WORK_DIR / "DS2" / "labels" / "validation" / "same.txt")
        self.assertTrue(is_inside(img, settings.RAW_DIR))
        self.assertFalse(is_inside(work_label_path(img), settings.RAW_DIR))             # 저장 위치는 RAW 밖이어야 한다

    def test_outside_raw_goes_to_a_separate_folder(self):
        outside = self.tmp / "other" / "x.jpg"
        self.assertEqual(locate_in_raw(outside), (None, None))
        self.assertEqual(work_label_path(outside), settings.WORK_DIR / "_RAW밖" / "x.txt")


if __name__ == "__main__":
    unittest.main()
