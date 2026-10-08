"""QA Summary 만들기(tools/qa_summary.py) 시험 — 가짜 폴더로 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_qa_summary.py
"""
import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools import qa_summary as qs

HEADER = ["No", "이미지 파일명", "이미지 유형", "상태", "발견된 문제", "작성자", "검수자", "출처 데이터셋", "원래 split"]


class QaSummaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.raw, self.work = self.tmp / "raw", self.tmp / "work"
        rows = []
        # a: 그대로 / b: 박스 추가 / c: Class 변경 / d: 박스 삭제
        data = {"a": ("1 0.5 0.5 0.2 0.2\n", None), "b": ("1 0.5 0.5 0.2 0.2\n", "1 0.5 0.5 0.2 0.2\n3 0.2 0.2 0.1 0.1\n"),
                "c": ("1 0.5 0.5 0.2 0.2\n", "2 0.5 0.5 0.2 0.2\n"), "d": ("1 0.5 0.5 0.2 0.2\n0 0.1 0.1 0.1 0.1\n", "1 0.5 0.5 0.2 0.2\n")}
        for i, (stem, (raw_txt, work_txt)) in enumerate(data.items(), 1):
            for kind in ("images", "labels"):
                (self.raw / "DS" / kind / "train").mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (100, 100)).save(self.raw / "DS" / "images" / "train" / f"{stem}.jpg")
            (self.raw / "DS" / "labels" / "train" / f"{stem}.txt").write_text(raw_txt, encoding="utf-8")
            if work_txt:
                (self.work / "DS" / "labels" / "train").mkdir(parents=True, exist_ok=True)
                (self.work / "DS" / "labels" / "train" / f"{stem}.txt").write_text(work_txt, encoding="utf-8")
            rows.append({"No": i, "이미지 파일명": f"{stem}.jpg", "이미지 유형": "김치+대상 객체", "상태": "수정 완료" if work_txt else "검수 완료",
                         "발견된 문제": "", "작성자": "가", "검수자": "나", "출처 데이터셋": "DS", "원래 split": "train"})
        self.manifest = self.tmp / "m.csv"
        with open(self.manifest, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=HEADER)
            w.writeheader()
            w.writerows(rows)

    def collect(self):
        return qs.collect(self.raw, self.work, self.manifest)

    def test_counts_added_modified_deleted_unchanged(self):
        s = self.collect()
        # a 그대로 1, b 그대로 1 + 추가 1, c 수정 1(Class 변경), d 그대로 1 + 삭제 1
        self.assertEqual({k: s["changes"][k] for k in ("그대로", "수정", "추가", "삭제")}, {"그대로": 3, "수정": 1, "추가": 1, "삭제": 1})
        self.assertEqual(s["changed_photos"], 3)
        self.assertEqual(s["status_mismatch"], 0)
        self.assertEqual(s["class_moves"], {(1, 2): 1})

    def test_class_totals_before_and_after(self):
        s = self.collect()
        self.assertEqual(sum(s["raw_cls"].values()), 5)
        self.assertEqual(sum(s["final_cls"].values()), 5)           # 추가 1 - 삭제 1
        self.assertEqual(s["final_cls"][3], 1)
        self.assertEqual(s["deleted_by_class"][0], 1)

    def test_markdown_has_the_key_numbers_and_no_file_names(self):
        md = qs.build_markdown(self.collect(), [])
        self.assertIn("전체 **4장**", md)
        self.assertIn("미처리 REVIEW **0건**", md)
        self.assertIn("검수일", md)
        self.assertNotIn("【기입】", md)
        self.assertNotIn("a.jpg", md)                                # 사진 파일명은 넣지 않는다
        self.assertIn("최종 FAIL **0건**", md)
        self.assertIn("교과 8 사용 가능", md)

    def test_unresolved_review_and_same_person_are_reported_as_fail(self):
        with open(self.manifest, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        rows[0].update({"상태": "수정 필요", "발견된 문제": "REVIEW: class_ambiguous"})
        rows[1]["검수자"] = rows[1]["작성자"]
        with open(self.manifest, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=HEADER)
            w.writeheader()
            w.writerows(rows)
        md = qs.build_markdown(self.collect(), [])
        self.assertIn("미처리 REVIEW **1건**", md)
        self.assertIn("**미달**", md)
        self.assertIn("미완료", md)                                   # 최종 QA 판정도 사용 불가로 나온다

    def test_inputs_are_not_modified(self):
        def snap(root):
            return sorted((p.relative_to(root).as_posix(), p.read_bytes()) for p in root.rglob("*") if p.is_file())
        before = (snap(self.raw), snap(self.work), self.manifest.read_bytes())
        qs.build_markdown(self.collect(), [])
        self.assertEqual((snap(self.raw), snap(self.work), self.manifest.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()
