"""결과 묶기(tools/pack_results.py) 시험 — 가짜 폴더로 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_pack_results.py
"""
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools import pack_results as pr


class PackResultsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = self.tmp / "work"
        d = self.work / "DS1" / "labels" / "train"
        d.mkdir(parents=True)
        (d / "a.txt").write_text("2 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        (d / "b.txt").write_text("", encoding="utf-8")                         # 빈 라벨도 정상이므로 포함
        (d / "a.txtZone.Identifier").write_text("[ZoneTransfer]\nZoneId=3\n")  # 넣지 않는다
        (self.work / "_session.json").write_text("{}", encoding="utf-8")        # 넣지 않는다
        (self.work / "DS1" / "photo.jpg").write_bytes(b"jpg")                   # 사진이 섞여 있어도 넣지 않는다
        self.manifest = self.tmp / "m.csv"
        self.manifest.write_text("No,이미지 파일명\n1,a.jpg\n2,b.jpg\n", encoding="utf-8-sig")

    def names(self, z):
        with zipfile.ZipFile(z) as f:
            return sorted(f.namelist())

    def test_only_labels_and_the_manifest_go_in(self):
        out = self.tmp / "out" / "r.zip"
        result = pr.pack(out, self.work, self.manifest)
        self.assertEqual(result, {"labels": 2, "manifest": 2, "skipped": 3})
        self.assertEqual(self.names(out), ["DS1/labels/train/a.txt", "DS1/labels/train/b.txt", "검수표.csv"])

    def test_folder_structure_and_contents_are_kept(self):
        out = self.tmp / "r.zip"
        pr.pack(out, self.work, self.manifest)
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.read("DS1/labels/train/a.txt").decode("utf-8"), "2 0.5 0.5 0.2 0.2\n")
            self.assertEqual(z.read("검수표.csv").decode("utf-8-sig").splitlines()[1], "1,a.jpg")

    def test_inputs_are_not_modified(self):
        before = sorted((p.relative_to(self.work).as_posix(), p.read_bytes()) for p in self.work.rglob("*") if p.is_file())
        pr.pack(self.tmp / "r.zip", self.work, self.manifest)
        after = sorted((p.relative_to(self.work).as_posix(), p.read_bytes()) for p in self.work.rglob("*") if p.is_file())
        self.assertEqual(before, after)

    def test_works_without_a_manifest_or_work_folder(self):
        result = pr.pack(self.tmp / "r.zip", self.work, self.tmp / "없음.csv")
        self.assertEqual((result["labels"], result["manifest"]), (2, None))
        empty = pr.pack(self.tmp / "e.zip", self.tmp / "없는폴더", self.tmp / "없음.csv")
        self.assertEqual((empty["labels"], empty["manifest"]), (0, None))

    def test_round_trip_with_import_labels(self):
        """묶은 파일을 풀어서 import_labels 로 받으면 같은 라벨이 들어온다"""
        from PIL import Image
        from tools import import_labels as il
        raw = self.tmp / "raw"
        d = raw / "DS1" / "images" / "train"
        d.mkdir(parents=True)
        for n in ("a.jpg", "b.jpg"):
            Image.new("RGB", (10, 10)).save(d / n)
        out = self.tmp / "r.zip"
        pr.pack(out, self.work, self.manifest)
        unpacked = self.tmp / "푼폴더"
        with zipfile.ZipFile(out) as z:
            z.extractall(unpacked)
        other_work = self.tmp / "other_work"
        result = il.plan_import(unpacked, raw, other_work)
        self.assertEqual(len(result["new"]), 2)
        il.apply_import(result)
        self.assertEqual((other_work / "DS1" / "labels" / "train" / "a.txt").read_text(encoding="utf-8"), "2 0.5 0.5 0.2 0.2\n")

    def test_command_line_reports_and_refuses_when_nothing_to_pack(self):
        old = (pr.settings.WORK_DIR, pr.settings.MANIFEST_PATH)
        pr.settings.WORK_DIR, pr.settings.MANIFEST_PATH = self.tmp / "없는work", self.tmp / "없음.csv"
        self.addCleanup(lambda: (setattr(pr.settings, "WORK_DIR", old[0]), setattr(pr.settings, "MANIFEST_PATH", old[1])))
        out = self.tmp / "비어.zip"
        self.assertEqual(pr.main(["-o", str(out)]), 2)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
