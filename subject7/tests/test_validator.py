"""Validation 검증 모듈 단위 테스트 (tests/test_validator.py).

실행: python -m unittest tests/test_validator.py
"""
import csv
import tempfile
import unittest
from pathlib import Path

from src import settings
from src.validation.validator import (
    parse_label_file,
    validate_dataset,
    validate_rows,
    write_report,
)


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_box_passes_without_critical(self):
        """정상적인 Class 0 BBox는 CRITICAL 오류가 없어야 한다."""
        rows = [(0, 0.5, 0.5, 0.2, 0.2)]
        errors = []
        res = validate_rows(rows, errors)
        criticals = [r for r in res if r[0] == "CRITICAL"]
        self.assertEqual(len(criticals), 0)

    def test_class_range_error(self):
        """0~6 범위를 벗어난 Class ID(예: 8, 99)는 CRITICAL CLASS_RANGE 로 검출되어야 한다."""
        rows = [(8, 0.5, 0.5, 0.2, 0.2)]
        res = validate_rows(rows, [])
        codes = [r[1] for r in res if r[0] == "CRITICAL"]
        self.assertIn("CLASS_RANGE", codes)

    def test_class_disabled_warning(self):
        """사용하지 않는 Class 4(고무장갑)는 WARNING CLASS_DISABLED 로 검출되어야 한다."""
        rows = [(4, 0.5, 0.5, 0.2, 0.2)]
        res = validate_rows(rows, [])
        codes = [r[1] for r in res if r[0] == "WARNING"]
        self.assertIn("CLASS_DISABLED", codes)

    def test_coord_range_error(self):
        """0~1 범위를 벗어난 좌표는 CRITICAL COORD_RANGE 로 검출되어야 한다."""
        rows = [(0, 1.25, 0.5, 0.2, 0.2)]
        res = validate_rows(rows, [])
        codes = [r[1] for r in res if r[0] == "CRITICAL"]
        self.assertIn("COORD_RANGE", codes)

    def test_box_out_of_image(self):
        """BBox 중심과 크기로 인해 이미지 경계 밖으로 튀어나간 경우 BOX_OUT_OF_IMAGE 검출되어야 한다."""
        # xc=0.95, w=0.2 -> x_max = 1.05 > 1.0
        rows = [(0, 0.95, 0.5, 0.2, 0.2)]
        res = validate_rows(rows, [])
        codes = [r[1] for r in res if r[0] == "CRITICAL"]
        self.assertIn("BOX_OUT_OF_IMAGE", codes)

    def test_size_invalid(self):
        """Width 또는 Height 가 0 이하이면 CRITICAL SIZE_INVALID 로 검출되어야 한다."""
        rows = [(0, 0.5, 0.5, 0.0, 0.2)]
        res = validate_rows(rows, [])
        codes = [r[1] for r in res if r[0] == "CRITICAL"]
        self.assertIn("SIZE_INVALID", codes)

    def test_duplicate_box(self):
        """같은 위치에 거의 겹치는 중복 박스(IoU >= 0.95)는 WARNING DUPLICATE_BOX 로 검출되어야 한다."""
        rows = [
            (1, 0.5, 0.5, 0.2, 0.2),
            (1, 0.501, 0.5, 0.2, 0.2),
        ]
        res = validate_rows(rows, [])
        codes = [r[1] for r in res if r[0] == "WARNING"]
        self.assertIn("DUPLICATE_BOX", codes)

    def test_tiny_box(self):
        """지나치게 미세한 크기의 박스는 WARNING TINY_BOX 로 검출되어야 한다."""
        rows = [(2, 0.5, 0.5, 0.001, 0.001)]
        res = validate_rows(rows, [])
        codes = [r[1] for r in res if r[0] == "WARNING"]
        self.assertIn("TINY_BOX", codes)

    def test_empty_label_info(self):
        """내용이 빈 라벨은 INFO EMPTY_LABEL 로 안내되어야 한다."""
        rows = []
        res = validate_rows(rows, [])
        codes = [r[1] for r in res if r[0] == "INFO"]
        self.assertIn("EMPTY_LABEL", codes)

    def test_parse_label_file_bad_format(self):
        """5개 값이 아니거나 숫자가 아닌 잘못된 파일 형식은 에러로 감지되어야 한다."""
        bad_file = self.temp_path / "bad.txt"
        bad_file.write_text("0 0.5 0.5 0.2\nnot_a_number 0.1 0.2 0.3 0.4\n", encoding="utf-8")
        rows, errors = parse_label_file(bad_file)
        err_codes = [e[1] for e in errors]
        self.assertIn("BAD_FORMAT", err_codes)
        self.assertIn("BAD_NUMBER", err_codes)

    def test_write_report(self):
        """보고서 CSV 저장이 정상 동작하고 헤더가 포함되어야 한다."""
        report = [
            {"severity": "CRITICAL", "code": "CLASS_RANGE", "relative_path": "a/b/c.txt", "line": 1, "message": "에러"}
        ]
        out_csv = self.temp_path / "test_report.csv"
        write_report(report, out_csv)
        self.assertTrue(out_csv.is_file())
        with open(out_csv, encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 1)
            self.assertEqual(reader[0]["code"], "CLASS_RANGE")


if __name__ == "__main__":
    unittest.main()
