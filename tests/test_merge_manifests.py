"""검수표 합치기(tools/merge_manifests.py) 시험 — 가짜 데이터로 확인한다.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_merge_manifests.py
"""
import csv
import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from PIL import Image

from src import settings
from src.manifest.manifest_writer import HEADERS, ManifestError, _save
from tools import merge_manifests as mm


def row(name, status="검수 전", ds="DS1", split="train", author="", reviewer="", date="", issue="", no="1"):
    r = {h: "" for h in HEADERS}
    r.update({"No": no, "이미지 파일명": name, "라벨(TXT) 파일명": name.replace(".jpg", ".txt"), "상태": status,
              "출처 데이터셋": ds, "원래 split": split, "작성자": author, "검수자": reviewer, "검수일": date, "발견된 문제": issue})
    return r


class MergeManifestsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def csv(self, name, rows):
        p = self.tmp / name
        _save(p, rows)
        return p

    def rows_of(self, p):
        with open(p, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def run_main(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = mm.main([str(a) for a in args])
        return code, buf.getvalue()

    def test_different_photos_are_combined_sorted_and_renumbered(self):
        a = self.csv("a.csv", [row("b.jpg", "수정 완료", no="1"), row("a.jpg", "검수 완료", no="2")])
        b = self.csv("b.csv", [row("c.jpg", "수정 완료", ds="DS2", split="validation", no="1")])
        merged, conflicts, dup = mm.merge(mm.load_inputs([a, b]))
        self.assertEqual([r["이미지 파일명"] for r in merged], ["a.jpg", "b.jpg", "c.jpg"])
        self.assertEqual([r["No"] for r in merged], ["1", "2", "3"])
        self.assertEqual((conflicts, dup), ([], 0))

    def test_identical_duplicate_is_merged_silently(self):
        a = self.csv("a.csv", [row("a.jpg", "검수 완료", author="동훈")])
        b = self.csv("b.csv", [row("a.jpg", "검수 완료", author="동훈", no="7")])        # No 만 다르다
        merged, conflicts, dup = mm.merge(mm.load_inputs([a, b]))
        self.assertEqual((len(merged), len(conflicts), dup), (1, 0, 1))

    def test_same_name_in_another_split_or_dataset_is_a_different_photo(self):
        a = self.csv("a.csv", [row("x.jpg", ds="DS1", split="train")])
        b = self.csv("b.csv", [row("x.jpg", ds="DS2", split="validation")])
        merged, conflicts, _ = mm.merge(mm.load_inputs([a, b]))
        self.assertEqual((len(merged), len(conflicts)), (2, 0))

    def test_conflict_prefers_reviewed_then_later_date_then_later_file(self):
        a = self.csv("a.csv", [row("p.jpg", "검수 전"), row("q.jpg", "수정 완료", date="2026-10-01"), row("r.jpg", "검수 완료", author="A")])
        b = self.csv("b.csv", [row("p.jpg", "수정 완료", author="B", date="2026-10-02"),
                               row("q.jpg", "수정 완료", date="2026-10-05", author="B"),
                               row("r.jpg", "검수 완료", author="B")])
        merged, conflicts, _ = mm.merge(mm.load_inputs([a, b]))
        by = {r["이미지 파일명"]: r for r in merged}
        self.assertEqual(by["p.jpg"]["작성자"], "B")                 # 검수 전 < 검수한 줄
        self.assertEqual(by["q.jpg"]["검수일"], "2026-10-05")        # 더 늦은 검수일
        self.assertEqual(by["r.jpg"]["작성자"], "B")                 # 같으면 뒤에 넣은 파일
        self.assertEqual(len(conflicts), 3)

    def test_first_file_wins_over_an_unreviewed_later_row(self):
        a = self.csv("a.csv", [row("p.jpg", "수정 완료", author="A", date="2026-10-02")])
        b = self.csv("b.csv", [row("p.jpg", "검수 전")])
        merged, _c, _d = mm.merge(mm.load_inputs([a, b]))
        self.assertEqual(merged[0]["작성자"], "A")

    def test_folder_input_and_inputs_are_not_modified(self):
        self.csv("a.csv", [row("a.jpg")])
        self.csv("b.csv", [row("b.jpg")])
        before = {p.name: p.read_bytes() for p in self.tmp.glob("*.csv")}
        out = self.tmp / "out" / "all.csv"
        code, text = self.run_main(self.tmp, "--apply", "-o", out)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.rows_of(out)), 2)
        self.assertEqual({p.name: p.read_bytes() for p in self.tmp.glob("*.csv")}, before)

    def test_preview_writes_nothing(self):
        a = self.csv("a.csv", [row("a.jpg")])
        out = self.tmp / "merged.csv"
        code, text = self.run_main(a, "-o", out)
        self.assertEqual(code, 0)
        self.assertFalse(out.exists())
        self.assertIn("미리보기", text)

    def test_default_output_is_the_programs_own_manifest(self):
        self.assertEqual(Path(mm.DEFAULT_OUTPUT).name, "dataset_manifest.csv")
        self.assertEqual(Path(mm.DEFAULT_OUTPUT).parent.name, "manifests")

    def test_existing_target_is_backed_up_and_its_rows_are_kept(self):
        """내 검수표가 저장할 파일일 때: 입력에 없어도 기존 줄이 사라지지 않고, 덮어쓰기 전 백업이 남는다"""
        target = self.csv("dataset_manifest.csv", [row("mine.jpg", "수정 완료", author="나", date="2026-10-07")])
        before = target.read_bytes()
        other = self.csv("동훈.csv", [row("theirs.jpg", "수정 완료", author="동훈")])
        code, text = self.run_main(other, "--apply", "-o", target)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(r["이미지 파일명"] for r in self.rows_of(target)), ["mine.jpg", "theirs.jpg"])
        backups = list(self.tmp.glob("dataset_manifest.백업-*.csv"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), before)                          # 백업은 덮어쓰기 전과 똑같다
        self.assertIn("함께 합칩니다", text)

    def test_target_listed_as_an_input_is_merged_once_and_backed_up(self):
        target = self.csv("dataset_manifest.csv", [row("a.jpg", "수정 완료", author="나")])
        other = self.csv("b.csv", [row("b.jpg")])
        code, _t = self.run_main(target, other, "--apply", "-o", target)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.rows_of(target)), 2)
        self.assertEqual(len(list(self.tmp.glob("dataset_manifest.백업-*.csv"))), 1)

    def test_default_output_path_is_used_when_not_given(self):
        target = self.tmp / "manifests" / "dataset_manifest.csv"
        old, mm.DEFAULT_OUTPUT = mm.DEFAULT_OUTPUT, target
        self.addCleanup(lambda: setattr(mm, "DEFAULT_OUTPUT", old))
        a = self.csv("a.csv", [row("a.jpg")])
        code, _t = self.run_main(a, "--apply")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.rows_of(target)), 1)

    def test_unreadable_existing_target_stops_without_changes(self):
        target = self.tmp / "dataset_manifest.csv"
        target.write_text("a,b\n1,2\n", encoding="utf-8")
        before = target.read_bytes()
        code, text = self.run_main(self.csv("a.csv", [row("a.jpg")]), "--apply", "-o", target)
        self.assertEqual(code, 2)
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(list(self.tmp.glob("*.백업-*")), [])

    def test_wrong_header_and_cp949_name_the_bad_file(self):
        good = self.csv("good.csv", [row("a.jpg")])
        bad = self.tmp / "bad.csv"
        bad.write_text("a,b\n1,2\n", encoding="utf-8")
        code, text = self.run_main(good, bad)
        self.assertEqual(code, 2)
        self.assertIn("[bad.csv]", text)
        bad.write_bytes("이미지,상태\n한글,완료\n".encode("cp949"))
        code, text = self.run_main(good, bad)
        self.assertEqual(code, 2)
        self.assertIn("[bad.csv]", text)

    def test_missing_input_is_reported(self):
        code, text = self.run_main(self.tmp / "없는.csv")
        self.assertEqual(code, 2)

    def test_summary_counts_and_missing_photos(self):
        raw = self.tmp / "raw"
        for ds, split, name in (("DS1", "train", "a.jpg"), ("DS1", "train", "b.jpg"), ("DS1", "train", "c.jpg")):
            d = raw / ds / "images" / split
            d.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (10, 10)).save(d / name)
        rows = [row("a.jpg", "검수 완료", author="A", reviewer="A"),
                row("b.jpg", "수정 필요", issue="REVIEW: class_ambiguous", author="")]
        s = mm.summarize(rows, raw_dir=raw)
        self.assertEqual((s["total"], s["no_author"], s["same_person"], s["open_review"]), (2, 1, 1, 1))
        self.assertEqual((s["raw_total"], s["missing"]), (3, 1))                  # c.jpg 의 줄이 없다
        self.assertEqual(s["status"], {"검수 완료": 1, "수정 필요": 1})

    def test_blank_rows_are_ignored(self):
        a = self.csv("a.csv", [row("a.jpg"), {h: "" for h in HEADERS}])
        merged, _c, _d = mm.merge(mm.load_inputs([a]))
        self.assertEqual(len(merged), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
