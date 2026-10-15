# `src/validation/validator.py`

> 데이터 조사(Inventory)와 무결성 검증(QA Validation). 오류를 고치지 않고 **보고만** 한다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../src/validation/validator.py)

## 역할

1. **데이터 조사** (`도구 ▸ 데이터 조사`): RAW 의 데이터셋·split 별 이미지 수, 라벨 수, 짝, 빈 TXT, 읽지 못한 줄, Class 분포
2. **무결성 검증** (`도구 ▸ QA 검증 (무결성)`): 사진마다 TXT 를 검사해 문제 목록을 만든다. **WORK 라벨이 있으면 WORK, 없으면 RAW** 를 검사한다.
3. 결과를 CSV 로 저장 (`reports/validation_report.csv`, Git 제외)

## 주요 구성요소

| 함수 | 입력 | 출력 | 설명 |
|---|---|---|---|
| `scan_inventory(raw_dir)` | RAW 경로 | `(rows, summary)` | `rows = [{dataset, split, image, label, pair, empty, bad}]`, `summary = {class_bbox, bad_lines, out_of_range}` |
| `inventory_markdown(rows, summary)` | 위 결과 | `str` | 데이터 조사표용 Markdown 표. 사용 안 하는 Class 가 있으면 "삭제하지 말고 REVIEW" 경고 |
| `_iou(a, b)` | YOLO 행 2개 | 0~1 | 비율 좌표 기준 IoU |
| `parse_label_file(path)` | TXT | `(rows, errors)` | `errors = [(줄 번호, BAD_FORMAT/BAD_NUMBER, 내용)]` |
| `validate_rows(rows, errors)` | 위 결과 | `[(severity, code, line, msg)]` | TXT 한 장 검사 |
| `validate_dataset(items=None, raw_dir=None, work_dir=None)` | – | `[dict]` | `items` 를 주면 그 목록만, 아니면 RAW 전체를 순회 |
| `write_report(report, path)` | 결과, 경로 | – | `severity, code, relative_path, line, message` 열의 `utf-8-sig` CSV |

### 검사 코드표

| 수준 | 코드 | 조건 |
|---|---|---|
| CRITICAL | `PAIR_MISSING_TXT` / `PAIR_MISSING_JPG` | 짝이 없음 |
| CRITICAL | `BAD_FORMAT` / `BAD_NUMBER` | 값이 5개가 아님 / 숫자로 바꿀 수 없음 |
| CRITICAL | `CLASS_RANGE` | Class 가 0 ~ (Class 수 − 1) 밖 |
| WARNING | `CLASS_DISABLED` | 사용 안 하는 Class (4) → REVIEW 대상 |
| CRITICAL | `COORD_RANGE` | xc, yc, w, h 중 0~1 밖 |
| CRITICAL | `SIZE_INVALID` | w 또는 h ≤ 0 (이후 검사 생략) |
| CRITICAL | `BOX_OUT_OF_IMAGE` | BBox 가장자리가 0~1 밖 (허용 오차 1e-6) |
| WARNING | `TINY_BOX` | w 또는 h < 0.002 |
| WARNING | `DUPLICATE_BOX` | 같은 Class, IoU ≥ 0.95 |
| INFO | `EMPTY_LABEL` | 빈 TXT — 정상 김치인지 확인 |

`relative_path` 는 `데이터셋/split/파일이름(확장자 없음)` 형식이며, 결과 창에서 더블클릭하면 [`data_paths.find_raw_image`](../data_paths.md) 로 그 사진을 연다.

## 의존성

- **사용하는 것**: [`settings`](../settings.md) (`CLASSES`, `UNUSED_CLASSES`, `IMAGE_EXTS`, `RAW_DIR`, `WORK_DIR`, `class_name`)
- **사용하는 곳**: [`ui/main_window`](../ui/main_window.md), `tools/` 의 [`build_final`](../../tools/build_final.md) · [`final_evidence`](../../tools/final_evidence.md) · [`import_labels`](../../tools/import_labels.md) · [`qa_summary`](../../tools/qa_summary.md), [`tests/test_validator`](../../tests/test_validator.md), [`tests/test_label_io`](../../tests/test_label_io.md), [`tests/day1_selftest`](../../tests/day1_selftest.md)

## 사용 예

```python
from src.validation.validator import validate_dataset, write_report

report = validate_dataset()                                    # RAW 전체 (WORK 우선)
critical = [r for r in report if r["severity"] == "CRITICAL"]
write_report(report, "reports/validation_report.csv")
```

## 주의사항

- **Class 번호 해석이 화면과 다르다.** `parse_label_file` 과 `scan_inventory` 는 `int()` 만 쓰므로 `2.0` 같은 Class 를 `BAD_NUMBER` 로 본다. 화면([`yolo_loader.parse_class_id`](../yolo/yolo_loader.md))은 같은 줄을 Class 2 로 읽는다.
- 짝 검사는 이미지와 **RAW 라벨** 의 이름 목록을 기준으로 한다. RAW 에 없고 WORK 에만 있는 TXT 는 `PAIR_MISSING_JPG` 로 잡히지 않는다.
- `scan_inventory` 는 RAW 라벨만 센다. 작업 진행 상황이 아니라 받은 데이터의 상태를 본다.
- `items` 모드는 `effective_label` / `label_path` / `key` 속성을 가진 객체를 받는다. 현재 화면은 이 모드를 쓰지 않고 RAW 전체 모드를 쓴다.
- `write_report` 는 원자적 저장이 아니다 (언제든 다시 만들 수 있는 산출물).
