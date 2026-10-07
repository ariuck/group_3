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
        self.assertEqual(result, {"labels": 2, "manifest": 2, "skipped": 3, "out_of_range": 0})
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

    # ── 이름과 번호 범위: 세 명의 결과를 한 곳에 풀어도 겹치거나 덮어쓰지 않도록 ──────────────────────
    def make_range_fixture(self):
        """사진 6장(DS1/train 4장 + DS2/validation 2장), 라벨·검수표 모두 6줄"""
        from PIL import Image
        from src.manifest.manifest_writer import HEADERS
        import csv as _csv
        raw = self.tmp / "rraw"
        names = [("DS1", "train", f"p{i}.jpg") for i in range(1, 5)] + [("DS2", "validation", f"q{i}.jpg") for i in range(1, 3)]
        work = self.tmp / "rwork"
        rows = []
        for ds, split, n in names:
            d = raw / ds / "images" / split
            d.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (10, 10)).save(d / n)
            lab = work / ds / "labels" / split
            lab.mkdir(parents=True, exist_ok=True)
            (lab / (n[:-4] + ".txt")).write_text(f"1 0.5 0.5 0.1 0.1\\n# {n}\\n", encoding="utf-8")
            r = {h: "" for h in HEADERS}
            r.update({"이미지 파일명": n, "출처 데이터셋": ds, "원래 split": split, "상태": "수정 완료", "비고(수정 내용)": "줄1\\n줄2"})
            rows.append(r)
        manifest = self.tmp / "rm.csv"
        from src.manifest.manifest_writer import _save
        _save(manifest, rows)
        return raw, work, manifest

    def test_number_range_keeps_only_that_range_of_labels_and_rows(self):
        raw, work, manifest = self.make_range_fixture()
        out = self.tmp / "범위.zip"
        result = pr.pack(out, work, manifest, name="이후영", number_range=(2, 5), raw_dir=raw)
        self.assertEqual((result["labels"], result["manifest"], result["out_of_range"]), (4, 4, 2))
        self.assertEqual(self.names(out), ["DS1/labels/train/p2.txt", "DS1/labels/train/p3.txt", "DS1/labels/train/p4.txt",
                                           "DS2/labels/validation/q1.txt", "검수표_이후영.csv"])
        import csv as _csv, io
        with zipfile.ZipFile(out) as z:
            rows = list(_csv.DictReader(io.StringIO(z.read("검수표_이후영.csv").decode("utf-8-sig"), newline="")))
        self.assertEqual([r["이미지 파일명"] for r in rows], ["p2.jpg", "p3.jpg", "p4.jpg", "q1.jpg"])
        self.assertEqual(rows[0]["비고(수정 내용)"], "줄1\\n줄2")               # 칸 안의 줄바꿈도 그대로

    def test_three_people_ranges_do_not_overlap_when_unpacked_together(self):
        raw, work, manifest = self.make_range_fixture()
        for who, rng in (("김동훈", (1, 2)), ("이후영", (3, 4)), ("지혜성", (5, 6))):
            pr.pack(self.tmp / f"{who}.zip", work, manifest, name=who, number_range=rng, raw_dir=raw)
        together = self.tmp / "모음"
        for who in ("김동훈", "이후영", "지혜성"):
            with zipfile.ZipFile(self.tmp / f"{who}.zip") as z:
                self.assertEqual(set(z.namelist()) & {n for w in ("김동훈", "이후영", "지혜성") if w != who
                                                       for n in zipfile.ZipFile(self.tmp / f"{w}.zip").namelist()}, set())
                z.extractall(together)
        labels = sorted(p.name for p in together.rglob("*.txt"))
        self.assertEqual(labels, ["p1.txt", "p2.txt", "p3.txt", "p4.txt", "q1.txt", "q2.txt"])          # 빠짐없이, 한 번씩
        self.assertEqual(sorted(p.name for p in together.glob("*.csv")), ["검수표_김동훈.csv", "검수표_이후영.csv", "검수표_지혜성.csv"])

    def test_bad_range_is_refused(self):
        raw, work, manifest = self.make_range_fixture()
        for bad in ((0, 3), (5, 9), (4, 2)):
            with self.assertRaises(ValueError):
                pr.pack(self.tmp / "x.zip", work, manifest, number_range=bad, raw_dir=raw)

    def test_command_line_needs_both_from_and_to(self):
        self.assertEqual(pr.main(["--from", "1"]), 2)

    def test_command_line_reports_and_refuses_when_nothing_to_pack(self):
        old = (pr.settings.WORK_DIR, pr.settings.MANIFEST_PATH)
        pr.settings.WORK_DIR, pr.settings.MANIFEST_PATH = self.tmp / "없는work", self.tmp / "없음.csv"
        self.addCleanup(lambda: (setattr(pr.settings, "WORK_DIR", old[0]), setattr(pr.settings, "MANIFEST_PATH", old[1])))
        out = self.tmp / "비어.zip"
        self.assertEqual(pr.main(["-o", str(out)]), 2)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
