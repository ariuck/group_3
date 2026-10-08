"""최종본 만들기(tools/build_final.py) 시험 — 가짜 폴더로 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_build_final.py
"""
import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools import build_final as bf

HEADER = ["No", "이미지 파일명", "상태", "작성자", "검수자", "출처 데이터셋", "원래 split"]


class BuildFinalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.raw, self.work, self.final = self.tmp / "raw", self.tmp / "work", self.tmp / "final"
        self.manifest = self.tmp / "m.csv"
        self.rows = []
        for ds, split, stem in (("DS1", "train", "a"), ("DS1", "train", "b"), ("DS2", "validation", "c")):
            img = self.raw / ds / "images" / split
            lbl = self.raw / ds / "labels" / split
            img.mkdir(parents=True, exist_ok=True)
            lbl.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (40, 40), "white").save(img / f"{stem}.jpg")
            (lbl / f"{stem}.txt").write_text("1 0.5 0.5 0.2 0.2\n", encoding="utf-8")
            self.rows.append({"No": str(len(self.rows) + 1), "이미지 파일명": f"{stem}.jpg", "상태": "검수 완료",
                              "작성자": "가", "검수자": "나", "출처 데이터셋": ds, "원래 split": split})
        w = self.work / "DS1" / "labels" / "train"
        w.mkdir(parents=True)
        (w / "a.txt").write_text("2 0.4 0.4 0.2 0.2\n", encoding="utf-8")        # 검수하며 고친 라벨
        self.write_manifest()

    def write_manifest(self):
        with open(self.manifest, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=HEADER)
            w.writeheader()
            w.writerows(self.rows)

    def check(self):
        return bf.check(self.raw, self.work, self.manifest)

    def test_ok_when_everything_is_reviewed(self):
        r = self.check()
        self.assertEqual(r["blocked"], {})
        self.assertEqual(len(r["items"]), 3)
        self.assertEqual(r["raw_labels"], 2)                                     # work 에 없는 라벨 2개는 RAW 라벨

    def test_unreviewed_status_blocks(self):
        for status in ("검수 전", "수정 필요", "제외"):
            self.rows[1]["상태"] = status
            self.write_manifest()
            self.assertEqual(len(self.check()["blocked"]), 1, status)

    def test_missing_reviewer_and_same_person_block(self):
        self.rows[0]["검수자"] = ""
        self.rows[1]["검수자"] = self.rows[1]["작성자"]
        self.write_manifest()
        blocked = self.check()["blocked"]
        self.assertIn("검수자 칸이 비어 있음", blocked)
        self.assertIn("작성자와 검수자가 같음", blocked)

    def test_photo_without_manifest_row_blocks(self):
        del self.rows[2]
        self.write_manifest()
        self.assertIn("검수표에 줄이 없음", self.check()["blocked"])

    def test_missing_manifest_blocks(self):
        self.manifest.unlink()
        blocked = self.check()["blocked"]
        self.assertTrue(any("검수표" in k for k in blocked))
        self.assertEqual(self.check()["items"], [])

    def test_critical_validation_error_blocks(self):
        (self.work / "DS1" / "labels" / "train" / "a.txt").write_text("9 0.5 0.5 0.2 0.2\n", encoding="utf-8")   # Class 범위 밖
        self.assertTrue(any("Validation" in k for k in self.check()["blocked"]))

    def test_build_keeps_structure_and_uses_reviewed_labels(self):
        done = bf.build(self.check(), self.final, classes=[{"name": "x"}, {"name": "y"}])
        self.assertEqual(done["photos"], 3)
        self.assertTrue((self.final / "DS1" / "images" / "train" / "a.jpg").is_file())
        self.assertTrue((self.final / "DS2" / "images" / "validation" / "c.jpg").is_file())     # train/validation 을 섞지 않는다
        self.assertEqual((self.final / "DS1" / "labels" / "train" / "a.txt").read_text(encoding="utf-8"), "2 0.4 0.4 0.2 0.2\n")
        self.assertEqual((self.final / "DS1" / "labels" / "train" / "b.txt").read_text(encoding="utf-8"), "1 0.5 0.5 0.2 0.2\n")
        self.assertEqual((self.final / "classes.txt").read_text(encoding="utf-8"), "x\ny\n")
        with open(self.final / "검수표.csv", encoding="utf-8-sig", newline="") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 3)

    def test_images_are_identical_copies_and_raw_is_untouched(self):
        def snapshot(root):
            return sorted((p.relative_to(root).as_posix(), p.read_bytes()) for p in root.rglob("*") if p.is_file())
        raw_before, work_before = snapshot(self.raw), snapshot(self.work)
        bf.build(self.check(), self.final)
        self.assertEqual(snapshot(self.raw), raw_before)
        self.assertEqual(snapshot(self.work), work_before)
        self.assertEqual((self.final / "DS1" / "images" / "train" / "a.jpg").read_bytes(),
                         (self.raw / "DS1" / "images" / "train" / "a.jpg").read_bytes())

    def test_build_refuses_when_blocked(self):
        self.rows[0]["상태"] = "검수 전"
        self.write_manifest()
        with self.assertRaises(ValueError):
            bf.build(self.check(), self.final)
        self.assertFalse(self.final.exists())

    def test_existing_final_needs_overwrite_and_is_backed_up(self):
        bf.build(self.check(), self.final)
        with self.assertRaises(FileExistsError):
            bf.build(self.check(), self.final)
        backup = self.tmp / "backup"
        done = bf.build(self.check(), self.final, overwrite=True, backup_dir=backup)
        self.assertEqual(done["moved_old_to"], backup)
        self.assertTrue((backup / "DS1" / "images" / "train" / "a.jpg").is_file())
        self.assertTrue((self.final / "DS1" / "images" / "train" / "a.jpg").is_file())

    def test_empty_skeleton_is_not_existing_content(self):
        (self.final / "DS1" / "images" / "train").mkdir(parents=True)
        (self.final / ".gitkeep").write_text("")
        self.assertEqual(bf.existing_content(self.final), 0)
        bf.build(self.check(), self.final)                                      # --overwrite 없이도 만들어진다


if __name__ == "__main__":
    unittest.main()
