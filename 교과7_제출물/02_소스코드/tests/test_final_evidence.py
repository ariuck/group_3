"""최종본 증빙(tools/final_evidence.py) 시험 — 가짜 폴더로 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_final_evidence.py
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools import final_evidence as fe


class FinalEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "images").mkdir()
        (self.tmp / "labels").mkdir()
        for stem, txt in (("a", "1 0.5 0.5 0.2 0.2\n"), ("b", "1 0.5 0.5 0.2 0.2\n2 0.2 0.2 0.1 0.1\n"), ("c", "0 0.5 0.5 0.3 0.3\n")):
            Image.new("RGB", (20, 20)).save(self.tmp / "images" / f"{stem}.jpg")
            (self.tmp / "labels" / f"{stem}.txt").write_text(txt, encoding="utf-8")

    def test_counts_and_pairs(self):
        info = fe.inspect(self.tmp)
        self.assertEqual((info["images"], info["labels"], info["pairs"], info["boxes"]), (3, 3, 3, 4))
        self.assertEqual((info["only_image"], info["only_label"], info["empty"]), (0, 0, 0))
        self.assertEqual(info["classes"][1], 2)
        self.assertEqual(len(info["samples"]), 2)                 # 박스 수가 1개·2개인 예시만 (같은 박스 수는 건너뜀)

    def test_unpaired_files_are_counted(self):
        (self.tmp / "labels" / "c.txt").unlink()
        (self.tmp / "labels" / "z.txt").write_text("1 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        info = fe.inspect(self.tmp)
        self.assertEqual((info["pairs"], info["only_image"], info["only_label"]), (2, 1, 1))

    def test_bad_label_is_reported_and_markdown_has_no_file_names(self):
        (self.tmp / "labels" / "a.txt").write_text("9 0.5 0.5 0.2 0.2\n", encoding="utf-8")        # Class 범위 밖
        info = fe.inspect(self.tmp)
        self.assertTrue(any(sev == "CRITICAL" for sev, _ in info["issues"]))
        md = fe.build_markdown(info)
        self.assertNotIn("a.jpg", md)
        self.assertNotIn("a.txt", md)
        self.assertIn("【기입】", md)


if __name__ == "__main__":
    unittest.main()
