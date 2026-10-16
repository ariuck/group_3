# `tests/test_validator.py`

> Validation 모듈 단위 시험.

[← 코드 문서 목차](../README.md) · [코드 보기](../../tests/test_validator.py) · 대상: [`src/validation/validator`](../src/validation/validator.md)

## 실행

```bash
python -m unittest tests/test_validator.py
```

## 시험 내용 (`TestValidator`)

| 시험 | 기대 |
|---|---|
| `test_valid_box_passes_without_critical` | 정상 Class 0 BBox 는 CRITICAL 없음 |
| `test_class_range_error` | Class 8, 99 → CRITICAL `CLASS_RANGE` |
| `test_class_disabled_warning` | Class 4 → WARNING `CLASS_DISABLED` |
| `test_coord_range_error` | 0~1 밖 좌표 → CRITICAL `COORD_RANGE` |
| `test_box_out_of_image` | 경계 밖 → `BOX_OUT_OF_IMAGE` |
| `test_size_invalid` | w·h ≤ 0 → CRITICAL `SIZE_INVALID` |
| `test_duplicate_box` | IoU ≥ 0.95 → WARNING `DUPLICATE_BOX` |
| `test_tiny_box` | 아주 작은 BBox → WARNING `TINY_BOX` |
| `test_empty_label_info` | 빈 라벨 → INFO `EMPTY_LABEL` |
| `test_parse_label_file_bad_format` | 값 개수·숫자 오류 감지 |
| `test_write_report` | 보고서 CSV 저장 + 머리글 |

`validate_dataset` 전체 순회와 `scan_inventory` 는 [`day1_selftest`](day1_selftest.md) 와 도구 시험에서 간접적으로 확인한다.
