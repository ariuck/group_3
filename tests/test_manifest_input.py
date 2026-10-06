"""사람 칸 기록 시험 (④ 저장·상태) — record_save(human=...) 와 read_human.

프로젝트 맨 위 폴더(group_3)에서 실행:

    python3 tests/test_manifest_input.py

실제 data/raw 와 manifests/ 는 건드리지 않는다. 임시 폴더에 작은 TXT 와 검수표를 만들어 시험한다.
"""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.manifest import manifest_writer  # noqa: E402
from src.manifest.manifest_writer import (  # noqa: E402
    FORM_FIELDS,
    HEADERS,
    ManifestError,
    read_human,
    record_save,
)

DATASET, SPLIT = "이물검출_학습데이터1", "train"
RAW_LABEL = "0 0.5 0.5 0.2 0.2\n"
EDITED_LABEL = "0 0.5 0.5 0.2 0.2\n3 0.3 0.3 0.1 0.1\n"


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


class ManifestInputTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.raw_dir, self.work_dir = root / "raw", root / "work"
        self.raw_dir.mkdir()
        self.work_dir.mkdir()
        self.manifest = root / "manifests" / "dataset_manifest.csv"
        # 임시 폴더의 이미지를 "RAW 안의 dataset1 / train" 으로 취급하게 한다.
        patcher = mock.patch.object(manifest_writer, "locate_in_raw", return_value=(DATASET, SPLIT))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def save(self, name="a.jpg", work_label=RAW_LABEL, human=None):
        """이미지 한 장을 [저장]한 것처럼 만든다. 돌려주는 값은 이미지 경로."""
        image = self.raw_dir / name
        raw_txt = self.raw_dir / (Path(name).stem + ".txt")
        work_txt = self.work_dir / (Path(name).stem + ".txt")
        raw_txt.write_text(RAW_LABEL, encoding="utf-8")
        work_txt.write_text(work_label, encoding="utf-8")
        screen_count = len(work_label.splitlines())
        record_save(image, raw_txt, work_txt, screen_count, manifest_path=self.manifest, human=human)
        return image

    def row(self, index=0):
        return read_csv(self.manifest)[1][index]

    # ---- 사람 칸 기록 ----------------------------------------------------

    def test_human_values_are_saved_and_read_back(self):
        human = {"작성자": "작업자A", "검수자": "검수자B", "이미지 유형": "김치+대상 객체",
                 "발견된 문제": "BBox 누락", "비고(수정 내용)": "작은 이물 1개 추가"}
        image = self.save(human=human)
        saved = read_human(image, manifest_path=self.manifest)
        for key, value in human.items():
            self.assertEqual(saved[key], value)
        self.assertEqual(sorted(saved), sorted(FORM_FIELDS))

    def test_auto_columns_are_still_filled(self):
        self.save(human={"작성자": "작업자A"})
        row = self.row()
        self.assertEqual(row["No"], "1")
        self.assertEqual(row["이미지 파일명"], "a.jpg")
        self.assertEqual(row["출처 데이터셋"], DATASET)
        self.assertEqual(row["원래 split"], SPLIT)
        self.assertEqual(row["원본 BBox 수"], "1")
        self.assertEqual(row["최종 BBox 수"], "1")

    def test_header_stays_the_same(self):
        self.save(human={"작성자": "작업자A"})
        self.assertEqual(read_csv(self.manifest)[0], HEADERS)

    def test_saving_again_updates_the_same_row(self):
        self.save(human={"비고(수정 내용)": "처음"})
        self.save(human={"비고(수정 내용)": "두 번째"})
        rows = read_csv(self.manifest)[1]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["No"], "1")
        self.assertEqual(rows[0]["비고(수정 내용)"], "두 번째")

    def test_without_human_keeps_what_was_entered(self):
        self.save(human={"작성자": "작업자A", "발견된 문제": "Class 오류"})
        self.save(human=None)
        row = self.row()
        self.assertEqual(row["작성자"], "작업자A")
        self.assertEqual(row["발견된 문제"], "Class 오류")

    def test_missing_key_is_untouched_and_blank_clears(self):
        self.save(human={"작성자": "작업자A", "검수자": "검수자B"})
        self.save(human={"검수자": ""})
        row = self.row()
        self.assertEqual(row["작성자"], "작업자A")
        self.assertEqual(row["검수자"], "")

    def test_auto_columns_cannot_be_overwritten_by_input(self):
        self.save(human={"No": "999", "출처 데이터셋": "바뀌면 안 됨", "원본 BBox 수": "50"})
        row = self.row()
        self.assertEqual(row["No"], "1")
        self.assertEqual(row["출처 데이터셋"], DATASET)
        self.assertEqual(row["원본 BBox 수"], "1")

    def test_two_images_do_not_mix(self):
        self.save("a.jpg", human={"작성자": "작업자A"})
        image_b = self.save("b.jpg", human={"작성자": "작업자B"})
        rows = read_csv(self.manifest)[1]
        self.assertEqual([r["No"] for r in rows], ["1", "2"])
        self.assertEqual(rows[0]["작성자"], "작업자A")
        self.assertEqual(read_human(image_b, manifest_path=self.manifest)["작성자"], "작업자B")

    def test_comma_quote_and_newline_survive(self):
        note = '쉼표, "따옴표"\n줄바꿈'
        image = self.save(human={"비고(수정 내용)": note.replace("\n", "\r\n")})
        saved = read_human(image, manifest_path=self.manifest)["비고(수정 내용)"]
        self.assertEqual(saved.replace("\r\n", "\n"), note)

    def test_unrecorded_image_reads_as_blank(self):
        self.save("a.jpg")
        other = self.raw_dir / "never_saved.jpg"
        self.assertEqual(read_human(other, manifest_path=self.manifest), {h: "" for h in FORM_FIELDS})

    def test_read_before_any_manifest_exists(self):
        image = self.raw_dir / "a.jpg"
        self.assertEqual(read_human(image, manifest_path=self.manifest), {h: "" for h in FORM_FIELDS})

    # ---- 상태 -------------------------------------------------------------

    def test_status_is_automatic_when_person_did_not_choose(self):
        self.save(work_label=RAW_LABEL, human={"작성자": "작업자A"})
        self.assertEqual(self.row()["상태"], "검수 전")
        self.save(work_label=EDITED_LABEL, human={"작성자": "작업자A", "상태": "검수 전"})
        self.assertEqual(self.row()["상태"], "수정 완료")

    def test_status_chosen_by_person_is_kept(self):
        self.save(work_label=EDITED_LABEL, human={"상태": "수정 필요"})
        self.assertEqual(self.row()["상태"], "수정 필요")
        self.save(work_label=EDITED_LABEL, human={"상태": "수정 필요"})
        self.assertEqual(self.row()["상태"], "수정 필요")

    def test_person_can_mark_review_done(self):
        self.save(work_label=EDITED_LABEL, human={})
        self.assertEqual(self.row()["상태"], "수정 완료")
        self.save(work_label=EDITED_LABEL, human={"상태": "검수 완료", "검수자": "검수자B"})
        row = self.row()
        self.assertEqual(row["상태"], "검수 완료")
        self.assertEqual(row["검수자"], "검수자B")

    def test_wrong_status_is_rejected_and_file_unchanged(self):
        self.save(human={"작성자": "작업자A"})
        before = self.manifest.read_bytes()
        with self.assertRaises(ManifestError):
            self.save(human={"상태": "DONE", "작성자": "바뀌면 안 됨"})
        self.assertEqual(self.manifest.read_bytes(), before)

    def test_no_temp_file_left_behind(self):
        self.save(human={"작성자": "작업자A"})
        self.assertEqual(os.listdir(self.manifest.parent), ["dataset_manifest.csv"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
