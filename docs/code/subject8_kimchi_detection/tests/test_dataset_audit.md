# `subject8_kimchi_detection/tests/test_dataset_audit.py`

> 임시 폴더에 가짜 데이터를 만들어 [`dataset_audit`](../src/dataset_audit.md)·[`leakage_check`](../src/leakage_check.md) 가 일부러 넣은 오류를 잡는지 확인한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../subject8_kimchi_detection/tests/test_dataset_audit.py)

## 실행

```bash
cd subject8_kimchi_detection
python -m unittest discover -s tests -v
```

실제 `data/subject7_final` 은 읽지도 건드리지도 않는다.

## 시험 내용

| 시험 | 확인 |
|---|---|
| `test_clean_data_has_no_issue` | 정상 데이터(BOM 이 붙은 TXT 포함)는 이슈 0, BBox 수·이미지별 BBox 분포·Class×장면 집계가 맞음 |
| `test_detects_injected_problems` | `BOX_OUT_OF_IMAGE`, `DUPLICATE_STEM`(train/validation 같은 이름), `EMPTY_NOT_NORMAL`, `NOT_IN_MANIFEST`, `CLASS_RANGE`, `CENTER_OUT_OF_RANGE`, `SIZE_OUT_OF_RANGE`, `CLASS4_REVIEW`, `COLUMN_COUNT` 를 정확히 잡음 |
| `test_empty_normal_kimchi_is_not_an_issue` | 검수표에 `정상 김치` 로 기록된 빈 TXT 는 이슈가 아님 |
| `test_counts_near_duplicates_within_and_across_groups` | 같은 그림 3장(같은 묶음 2장 + 다른 묶음 1장) → 같은 묶음 1쌍·다른 묶음 2쌍, 묶음별 원래 train/validation 수 |
