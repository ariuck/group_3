"""검수표(CSV) 기록의 까다로운 상황 시험 — 빈 파일·엑셀로 저장한 파일·특수 글자·검수일·경고창 반복.

실행 (프로젝트 폴더에서):  python -m unittest tests/test_manifest_edge.py
"""
import csv
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from PIL import Image

from src import settings
from src.manifest import manifest_writer as mf

ONE = "2 0.5 0.5 0.2 0.2\n"
TWO = ONE + "0 0.1 0.1 0.1 0.1\n"


class ManifestEdgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.old = (settings.RAW_DIR, settings.WORK_DIR)
        settings.RAW_DIR, settings.WORK_DIR = self.tmp / "raw", self.tmp / "work"
        self.addCleanup(lambda: (setattr(settings, "RAW_DIR", self.old[0]), setattr(settings, "WORK_DIR", self.old[1])))
        self.m = self.tmp / "m.csv"

    def photo(self, ds, split, name, raw_text, work_text):
        img = settings.RAW_DIR / ds / "images" / split / name
        img.parent.mkdir(parents=True, exist_ok=True)
        img.write_bytes(b"x")
        raw = None
        if raw_text is not None:
            raw = settings.RAW_DIR / ds / "labels" / split / (Path(name).stem + ".txt")
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text(raw_text, encoding="utf-8")
        work = settings.WORK_DIR / ds / "labels" / split / (Path(name).stem + ".txt")
        work.parent.mkdir(parents=True, exist_ok=True)
        work.write_text(work_text, encoding="utf-8")
        return img, raw, work

    def save(self, photo, count, human=None, today=None):
        img, raw, work = photo
        return mf.record_save(img, raw, work, count, manifest_path=self.m, human=human, today=today)

    def rows(self):
        with open(self.m, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    # ── 빈 파일 · 엑셀 ─────────────────────────────────────────
    def test_empty_file_is_treated_as_a_new_manifest(self):
        """(수정한 버그) 0바이트 검수표가 있으면 '머리글이 다릅니다' 오류로 저장이 완전히 막히던 문제"""
        self.m.write_bytes(b"")
        self.save(self.photo("DS1", "train", "a.jpg", TWO, ONE), 1)
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.rows()[0]["상태"], "수정 완료")
        self.assertEqual(mf.read_status_map(self.m), {("DS1", "train", "a.jpg"): "수정 완료"})

    def test_whitespace_only_file_is_also_new(self):
        self.m.write_text("\n\n", encoding="utf-8")
        self.save(self.photo("DS1", "train", "a.jpg", ONE, ONE), 1)
        self.assertEqual(len(self.rows()), 1)

    def test_wrong_header_is_still_refused_and_the_file_is_untouched(self):
        self.m.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
        before = self.m.read_bytes()
        with self.assertRaises(mf.ManifestError):
            self.save(self.photo("DS1", "train", "a.jpg", ONE, ONE), 1)
        self.assertEqual(self.m.read_bytes(), before)

    def test_excel_style_file_with_bom_and_crlf_is_accepted(self):
        self.save(self.photo("DS1", "train", "a.jpg", ONE, ONE), 1)
        text = self.m.read_text(encoding="utf-8-sig").replace("\n", "\r\n")
        self.m.write_bytes(("﻿" + text).encode("utf-8"))
        self.save(self.photo("DS1", "train", "b.jpg", ONE, ONE), 1)
        self.assertEqual([r["이미지 파일명"] for r in self.rows()], ["a.jpg", "b.jpg"])

    def test_rows_with_missing_or_extra_cells_do_not_break_saving(self):
        header = ",".join(mf.HEADERS)
        self.m.write_text(f"{header}\n1,short.jpg\n2,long.jpg,{','.join(['x'] * 30)}\n", encoding="utf-8-sig")
        self.save(self.photo("DS1", "train", "a.jpg", ONE, ONE), 1)
        names = [r["이미지 파일명"] for r in self.rows()]
        self.assertEqual(names, ["short.jpg", "long.jpg", "a.jpg"])
        self.assertTrue(all(set(r) == set(mf.HEADERS) for r in self.rows()))        # 모든 줄이 기준 19칸으로 정리된다
        self.assertEqual(self.rows()[0]["상태"], "")
        self.assertEqual(mf.read_status_map(self.m)[("", "", "short.jpg")], "")

    def test_cp949_file_gives_a_helpful_error(self):
        self.save(self.photo("DS1", "train", "a.jpg", ONE, ONE), 1)
        self.m.write_bytes(self.m.read_text(encoding="utf-8-sig").replace("검수 전", "한글").encode("cp949"))
        with self.assertRaises(mf.ManifestError) as cm:
            self.save(self.photo("DS1", "train", "b.jpg", ONE, ONE), 1)
        self.assertIn("CSV UTF-8", str(cm.exception))

    # ── 검수일 ────────────────────────────────────────────────
    def test_review_date_is_filled_when_the_review_is_done(self):
        """(수정한 문제) 검수일 칸이 영원히 비어 있어 제출 전에 손으로 적어야 하던 문제"""
        p = self.photo("DS1", "train", "a.jpg", TWO, TWO)
        self.save(p, 2, today=date(2026, 10, 6))
        self.assertEqual(self.rows()[0]["상태"], "검수 전")
        self.assertEqual(self.rows()[0]["검수일"], "")                       # 아직 검수한 것이 아니다
        self.save(p, 2, {"상태": "검수 완료"}, today=date(2026, 10, 7))
        self.assertEqual(self.rows()[0]["검수일"], "2026-10-07")

    def test_review_date_follows_every_finished_status(self):
        for i, status in enumerate(("검수 완료", "수정 필요", "제외")):
            p = self.photo("DS1", "train", f"s{i}.jpg", ONE, ONE)
            self.save(p, 1, {"상태": status}, today=date(2026, 1, 2 + i))
        self.assertEqual([r["검수일"] for r in self.rows()], ["2026-01-02", "2026-01-03", "2026-01-04"])
        edited = self.photo("DS1", "train", "e.jpg", TWO, ONE)
        self.save(edited, 1, today=date(2026, 2, 3))                         # 고쳐서 자동으로 '수정 완료'가 된 경우도
        self.assertEqual(self.rows()[-1]["상태"], "수정 완료")
        self.assertEqual(self.rows()[-1]["검수일"], "2026-02-03")

    def test_an_existing_date_is_never_overwritten(self):
        p = self.photo("DS1", "train", "a.jpg", ONE, ONE)
        self.save(p, 1, {"상태": "검수 완료"}, today=date(2026, 10, 6))
        rows = self.rows()
        rows[0]["검수일"] = "2025-12-25"                                      # 사람이 엑셀에서 고쳤다
        mf._save(self.m, rows)
        self.save(p, 1, {"상태": "제외"}, today=date(2026, 10, 9))
        self.assertEqual(self.rows()[0]["검수일"], "2025-12-25")

    def test_default_date_is_today(self):
        self.save(self.photo("DS1", "train", "a.jpg", ONE, ONE), 1, {"상태": "검수 완료"})
        self.assertEqual(self.rows()[0]["검수일"], date.today().isoformat())

    # ── 그 밖의 확인 ─────────────────────────────────────────
    def test_special_characters_come_back_unchanged(self):
        note = '쉼표, 따옴표 " 와\n줄바꿈, 한글 메모'
        self.save(self.photo("이물검출_학습데이터1", "train", "250410_가나다, 라.jpg", ONE, ONE), 1,
                  {"비고(수정 내용)": note, "작성자": "혜성"})
        r = self.rows()[0]
        self.assertEqual((r["비고(수정 내용)"], r["이미지 파일명"], r["작성자"]), (note, "250410_가나다, 라.jpg", "혜성"))

    def test_same_file_name_in_different_places_are_different_rows(self):
        for ds, split in (("DS1", "train"), ("DS1", "validation"), ("DS2", "train")):
            self.save(self.photo(ds, split, "a.jpg", ONE, ONE), 1)
        self.assertEqual([(r["출처 데이터셋"], r["원래 split"]) for r in self.rows()],
                         [("DS1", "train"), ("DS1", "validation"), ("DS2", "train")])
        self.assertEqual([r["No"] for r in self.rows()], ["1", "2", "3"])

    def test_saving_the_same_photo_again_updates_the_row_and_keeps_the_original_count(self):
        p = self.photo("DS1", "train", "a.jpg", TWO, TWO)
        self.save(p, 2)
        p[2].write_text(ONE, encoding="utf-8")
        self.save(p, 1)
        r = self.rows()
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["원본 BBox 수"], r[0]["최종 BBox 수"], r[0]["Class"]), ("2", "1", "2"))

    def test_human_chosen_review_status_survives_later_edits(self):
        p = self.photo("DS1", "train", "a.jpg", TWO, TWO)
        self.save(p, 2, {"상태": "수정 필요", "발견된 문제": "REVIEW: x"})
        p[2].write_text(ONE, encoding="utf-8")
        self.save(p, 1, {"상태": "수정 필요"})
        self.assertEqual(self.rows()[0]["상태"], "수정 필요")

    def test_outside_raw_is_not_recorded(self):
        outside = self.tmp / "other" / "x.jpg"
        outside.parent.mkdir()
        outside.write_bytes(b"x")
        work = self.tmp / "w.txt"
        work.write_text(ONE)
        msg = mf.record_save(outside, None, work, 1, manifest_path=self.m)
        self.assertIn("기록하지 않았습니다", msg)
        self.assertFalse(self.m.exists())


class ManifestWarningUiTest(unittest.TestCase):
    """검수표를 못 읽는 상태에서 사진을 넘길 때 경고창이 사진마다 뜨지 않는다."""

    def setUp(self):
        from src.ui import main_window as mw
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        ds = self.tmp / "raw" / "DS1"
        (ds / "images" / "train").mkdir(parents=True)
        (ds / "labels" / "train").mkdir(parents=True)
        for i in range(4):
            Image.new("RGB", (300, 200)).save(ds / "images" / "train" / f"a{i}.jpg")
        settings.RAW_DIR, settings.WORK_DIR, settings.MANIFEST_PATH = self.tmp / "raw", self.tmp / "work", self.tmp / "m.csv"
        self.warnings = []
        mw.messagebox.showwarning = lambda *a, **k: self.warnings.append(a[0])
        mw.messagebox.showerror = mw.messagebox.showinfo = lambda *a, **k: None
        try:
            self.root = mw.make_root()
        except Exception as e:
            self.skipTest(f"Tk 화면을 만들 수 없음: {e}")
        self.app = mw.Day1Labeler(self.root)
        self.root.update()
        self.files = sorted((ds / "images" / "train").glob("*.jpg"))

    def tearDown(self):
        self.app.shutdown()
        self.root.destroy()

    def test_warning_is_shown_once_per_broken_file(self):
        (self.tmp / "m.csv").write_text("가,나,다\n1,2,3\n", encoding="utf-8")        # 머리글이 다른 검수표
        for p in self.files:
            self.app.load_image(p)
        self.assertEqual(len(self.warnings), 1)                                       # 사진 4장을 열어도 경고창은 한 번
        self.assertIn("검수표(CSV)를 읽지 못해", self.app.warn_label.cget("text"))      # 대신 이미지 위 경고 줄에는 계속 보인다

    def test_after_fixing_the_file_a_new_problem_warns_again(self):
        m = self.tmp / "m.csv"
        m.write_text("가,나,다\n", encoding="utf-8")
        self.app.load_image(self.files[0])
        self.assertEqual(len(self.warnings), 1)
        m.write_text(",".join(mf.HEADERS) + "\n", encoding="utf-8")                    # 고쳤다 → 경고 없이 읽힘
        self.app.load_image(self.files[1])
        self.assertEqual(len(self.warnings), 1)
        self.assertNotIn("검수표", self.app.warn_label.cget("text"))                   # 읽히면 경고 줄도 사라진다
        import os
        m.write_text("또,다른,문제\n", encoding="utf-8")                                # 다시 망가졌다 → 다시 한 번 알린다
        os.utime(m, ns=(m.stat().st_atime_ns, m.stat().st_mtime_ns + 5_000_000_000))
        self.app.load_image(self.files[2])
        self.assertEqual(len(self.warnings), 2)


if __name__ == "__main__":
    unittest.main()
