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

    # ── 옛 라벨이 남아 있는 PC (실제로 검수표만 새것이 되고 라벨은 원본 그대로이던 문제) ─────────────
    def run_main(self, *args):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = il.main([str(a) for a in args])
        return code, buf.getvalue()

    def stale_setup(self):
        """내 PC 에 옛 라벨이 이미 있고, 받은 폴더에는 수정된 새 라벨이 있다."""
        self.put("a.txt", OTHER)                                    # 받은 것 (새 라벨)
        old = self.work / "DS1" / "labels" / "train" / "a.txt"
        old.parent.mkdir(parents=True)
        old.write_text(GOOD, encoding="utf-8")                      # 내 PC 의 옛 라벨
        return old

    def test_apply_without_overwrite_leaves_stale_labels_and_warns_loudly(self):
        old = self.stale_setup()
        settings_work, settings_raw = il.settings.WORK_DIR, il.settings.RAW_DIR
        il.settings.WORK_DIR, il.settings.RAW_DIR = self.work, self.raw
        self.addCleanup(lambda: (setattr(il.settings, "WORK_DIR", settings_work), setattr(il.settings, "RAW_DIR", settings_raw)))
        code, text = self.run_main(self.src, "--apply")
        self.assertEqual(code, 0)
        self.assertEqual(old.read_text(encoding="utf-8"), GOOD)             # 옛 라벨이 그대로
        self.assertIn("복사하지 않고 그대로 두었습니다", text)
        self.assertIn("--apply --overwrite", text)                          # 다시 실행할 명령까지 알려 준다

    def test_overwrite_replaces_stale_labels_and_backs_them_up(self):
        old = self.stale_setup()
        result = self.plan()
        backup = self.tmp / "백업"
        n = il.apply_import(result, overwrite=True, backup_dir=backup)
        self.assertEqual(n, 1)
        self.assertEqual(old.read_text(encoding="utf-8"), OTHER)            # 새 라벨로 바뀜
        self.assertEqual((backup / "a.txt").read_text(encoding="utf-8"), GOOD)   # 덮어쓰기 전 파일이 백업에 남음

    def test_backup_keeps_files_with_the_same_name_from_different_folders(self):
        self.put("a.txt", OTHER)
        self.put("c.txt", OTHER)
        for ds, split, name in (("DS1", "train", "a.txt"), ("DS2", "validation", "c.txt")):
            p = self.work / ds / "labels" / split / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(GOOD, encoding="utf-8")
        backup = self.tmp / "백업2"
        il.apply_import(self.plan(), overwrite=True, backup_dir=backup)
        self.assertEqual(sorted(p.name for p in backup.rglob("*.txt")), ["a.txt", "c.txt"])

    def test_no_backup_when_nothing_is_overwritten(self):
        self.put("a.txt")
        backup = self.tmp / "백업3"
        il.apply_import(self.plan(), overwrite=True, backup_dir=backup)       # 새 라벨뿐이면 덮어쓸 것이 없다
        self.assertFalse(backup.exists())

    def test_command_line_preview_and_missing_folder(self):
        self.put("a.txt")
        self.assertEqual(il.main([str(self.tmp / "없는폴더")]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
