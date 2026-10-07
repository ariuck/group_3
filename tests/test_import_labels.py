"""라벨 가져오기(tools/import_labels.py) 시험 — 가짜 raw/work 폴더로 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_import_labels.py
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools import import_labels as il

GOOD = "2 0.5 0.5 0.2 0.2\n"
OTHER = "3 0.4 0.4 0.1 0.1\n"


class ImportLabelsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.raw, self.work, self.src = self.tmp / "raw", self.tmp / "work", self.tmp / "받은"
        self.src.mkdir()
        for ds, split, name in (("DS1", "train", "a.jpg"), ("DS1", "train", "b.jpg"), ("DS2", "validation", "c.jpg"),
                                ("DS1", "train", "dup.jpg"), ("DS2", "validation", "dup.jpg")):
            d = self.raw / ds / "images" / split
            d.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (10, 10)).save(d / name)

    def put(self, rel, text=GOOD):
        p = self.src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def plan(self):
        return il.plan_import(self.src, self.raw, self.work)

    def test_new_labels_go_to_the_matching_dataset_and_split(self):
        self.put("a.txt")                                          # 폴더 구조 없이 이름만 있어도 raw 의 사진으로 위치를 찾는다
        self.put("x/y/c.txt")
        r = self.plan()
        self.assertEqual(sorted(t.relative_to(self.work).as_posix() for _s, t in r["new"]),
                         ["DS1/labels/train/a.txt", "DS2/labels/validation/c.txt"])
        n = il.apply_import(r)
        self.assertEqual(n, 2)
        self.assertEqual((self.work / "DS1" / "labels" / "train" / "a.txt").read_text(encoding="utf-8"), GOOD)

    def test_zone_identifier_files_are_ignored_and_never_created(self):
        self.put("a.txt")
        (self.src / "a.txtZone.Identifier").write_text("[ZoneTransfer]\nZoneId=3\n")
        (self.src / "b.txtZone.Identifier").write_text("[ZoneTransfer]\nZoneId=3\n")
        r = self.plan()
        self.assertEqual(r["_ignored"], 2)
        il.apply_import(r)
        names = [p.name for p in self.work.rglob("*") if p.is_file()]
        self.assertEqual(names, ["a.txt"])

    def test_preview_copies_nothing(self):
        self.put("a.txt")
        self.plan()
        self.assertFalse(self.work.exists())

    def test_same_content_is_not_a_conflict_and_different_content_is_held(self):
        self.put("a.txt")
        self.put("b.txt", OTHER)
        il.apply_import(self.plan())
        (self.work / "DS1" / "labels" / "train" / "b.txt").write_text(GOOD, encoding="utf-8")     # 작업 폴더의 b 를 다르게 바꿔 둔다
        r = self.plan()
        self.assertEqual([s.name for s, _t in r["same"]], ["a.txt"])
        self.assertEqual([s.name for s, _t in r["conflict"]], ["b.txt"])
        self.assertEqual(il.apply_import(r), 0)                                                    # 기본은 덮어쓰지 않는다
        self.assertEqual((self.work / "DS1" / "labels" / "train" / "b.txt").read_text(encoding="utf-8"), GOOD)
        self.assertEqual(il.apply_import(r, overwrite=True), 1)
        self.assertEqual((self.work / "DS1" / "labels" / "train" / "b.txt").read_text(encoding="utf-8"), OTHER)

    def test_unknown_invalid_and_ambiguous_are_reported_not_copied(self):
        self.put("nothing.txt")                                    # raw 에 같은 이름의 사진이 없다
        self.put("a.txt", "9 0.5 0.5 0.2 0.2\n")                   # Class 범위 밖
        self.put("dup.txt")                                        # 같은 이름의 사진이 두 곳에 있다
        r = self.plan()
        self.assertEqual([s.name for s, _w in r["unknown"]], ["nothing.txt"])
        self.assertEqual([s.name for s, _w in r["invalid"]], ["a.txt"])
        self.assertEqual([s.name for s, _w in r["ambiguous"]], ["dup.txt"])
        self.assertEqual(il.apply_import(r), 0)

    def test_path_hints_resolve_duplicate_names(self):
        self.put("DS2/labels/validation/dup.txt")
        r = self.plan()
        self.assertEqual([t.relative_to(self.work).as_posix() for _s, t in r["new"]], ["DS2/labels/validation/dup.txt"])

    def test_raw_is_never_modified(self):
        before = sorted((p.relative_to(self.raw).as_posix(), p.stat().st_mtime_ns) for p in self.raw.rglob("*") if p.is_file())
        self.put("a.txt")
        il.apply_import(self.plan())
        after = sorted((p.relative_to(self.raw).as_posix(), p.stat().st_mtime_ns) for p in self.raw.rglob("*") if p.is_file())
        self.assertEqual(before, after)

    def test_command_line_preview_and_missing_folder(self):
        self.put("a.txt")
        self.assertEqual(il.main([str(self.tmp / "없는폴더")]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
