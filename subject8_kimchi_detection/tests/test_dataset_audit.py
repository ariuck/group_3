"""DatasetAuditor · leakage_check 가 일부러 넣은 오류를 잡는지 가짜 데이터로 확인한다.

    cd subject8_kimchi_detection
    python -m unittest discover -s tests -v
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset_audit import DatasetAuditor  # noqa: E402
from src.leakage_check import run_leakage_check  # noqa: E402


def write_manifest(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["이미지 파일명", "이미지 유형", "출처 데이터셋", "원래 split"])
        w.writerows(rows)


class DatasetAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "final"
        for d in ("images/train", "images/validation", "labels/train", "labels/validation"):
            (self.root / d).mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, split, stem, label_bytes):
        (self.root / "images" / split / f"{stem}.jpg").write_bytes(b"x")
        (self.root / "labels" / split / f"{stem}.txt").write_bytes(label_bytes)

    def run_audit(self):
        res = DatasetAuditor(self.root, Path(self.tmp.name) / "reports").run_audit()
        with open(res["issue_csv"], encoding="utf-8") as f:
            issues = sorted((r["file"], r["issue"]) for r in csv.DictReader(f))
        return res, issues

    def test_clean_data_has_no_issue(self):
        self.make("train", "a", b"2 0.5 0.5 0.1 0.1\n0 0.2 0.2 0.1 0.1\n")
        self.make("validation", "b", b"\xef\xbb\xbf5 0.5 0.5 0.1 0.1\n")  # BOM 이 붙어도 정상
        write_manifest(self.root / "검수표.csv", [["a.jpg", "김치+대상 객체", "d1", "train"],
                                                  ["b.jpg", "김치+대상 객체", "d2", "validation"]])
        res, issues = self.run_audit()
        self.assertEqual(issues, [])
        self.assertEqual(res["total_bboxes"], 3)
        self.assertEqual(res["bbox_distribution"], {1: 1, 2: 1})
        self.assertEqual(res["class_scene"][5], {"김치+대상 객체": 1})

    def test_detects_injected_problems(self):
        self.make("train", "edge", b"1 0.98 0.5 0.1 0.1\n")        # 오른쪽 끝 1.03
        self.make("train", "dup", b"2 0.5 0.5 0.1 0.1\n")
        self.make("validation", "dup", b"2 0.5 0.5 0.1 0.1\n")     # 다른 split, 같은 이름
        self.make("validation", "empty", b"")                       # 빈 TXT 인데 정상 김치가 아님
        self.make("validation", "norec", b"5 0.5 0.5 0.1 0.1\n")   # 검수표에 없음
        self.make("train", "bad", b"7 1.2 0.5 0 0.1\n4 0.5 0.5 0.1 0.1\n2 0.5 0.5\n")
        write_manifest(self.root / "검수표.csv", [[f"{s}.jpg", "김치+대상 객체", "d", "train"]
                                                  for s in ("edge", "dup", "empty", "bad")])
        _, issues = self.run_audit()
        self.assertEqual(issues, sorted([
            ("edge", "BOX_OUT_OF_IMAGE"),
            ("dup", "DUPLICATE_STEM"), ("dup", "DUPLICATE_STEM"),
            ("empty", "EMPTY_NOT_NORMAL"),
            ("norec", "NOT_IN_MANIFEST"),
            ("bad", "CLASS_RANGE"), ("bad", "CENTER_OUT_OF_RANGE"), ("bad", "SIZE_OUT_OF_RANGE"),
            ("bad", "CLASS4_REVIEW"), ("bad", "COLUMN_COUNT"),
        ]))

    def test_empty_normal_kimchi_is_not_an_issue(self):
        self.make("train", "clean", b"")
        write_manifest(self.root / "검수표.csv", [["clean.jpg", "정상 김치", "d", "train"]])
        res, issues = self.run_audit()
        self.assertEqual(issues, [])
        self.assertEqual(res["empty_labels"], 1)


class LeakageCheckTest(unittest.TestCase):
    def test_counts_near_duplicates_within_and_across_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            img_dir = Path(tmp) / "images"
            img_dir.mkdir()

            def save(name, fn):
                im = Image.new("L", (64, 64))
                im.putdata([fn(x, y) for y in range(64) for x in range(64)])
                im.save(img_dir / name, "JPEG")

            save("250101_100000000000.jpg", lambda x, y: x * 4)          # 가로 그라데이션
            save("250101_100010000000.jpg", lambda x, y: x * 4)          # 같은 그림, 같은 묶음
            save("250101_120000000000.jpg", lambda x, y: x * 4)          # 같은 그림, 다른 묶음 → 누수
            save("250101_130000000000.jpg", lambda x, y: 255 - x * 4)    # 반대 그라데이션
            df = pd.DataFrame({
                "이미지 파일명": sorted(p.name for p in img_dir.iterdir()),
                "capture_group": ["G00", "G00", "G01", "G02"],
                "원래 split": ["train", "validation", "train", "train"],
                "이미지 유형": ["김치+대상 객체"] * 4,
            })
            res = run_leakage_check(df, img_dir, Path(tmp) / "reports", workers=1)
            self.assertEqual(res["capture_groups"], 3)
            self.assertEqual(res["near_duplicate_pairs_within_group"], 1)
            self.assertEqual(res["near_duplicate_pairs_across_group"], 2)
            g00 = next(g for g in res["groups"] if g["capture_group"] == "G00")
            self.assertEqual((g00["original_train"], g00["original_validation"]), (1, 1))
            self.assertTrue(Path(res["leakage_csv"]).is_file())


if __name__ == "__main__":
    unittest.main()
