# `subject8_kimchi_detection/src/dataset_audit.py`

> 교과 7 최종본의 YOLO 라벨을 점검하는 `DatasetAuditor`. 짝·열 개수·Class 범위·Class 4·좌표 범위를 검사하고 요약·이슈 CSV 를 만든다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../subject8_kimchi_detection/src/dataset_audit.py)

## 역할

- 교과 8 에서 학습 전에 넘겨받은 데이터가 학습 가능한 상태인지 확인한다.
- 교과 7 의 [`validator`](../../src/validation/validator.md) 와 비슷한 검사를 교과 8 쪽에서 독립적으로 다시 한다 (영문 Class 이름 사용).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `CLASS_NAMES` | `{0: leaf_paper, 1: plastic_stone_metal, 2: branch, 3: insect, 4: rubber_glove_unused, 5: disease_browning, 6: green_onion_pepper}` |
| `DatasetAuditor(data_root, report_dir)` | `data_root/images`, `data_root/labels`, `data_root/검수표.csv` 를 읽음. 보고서 폴더 생성 |
| `.validate_yolo_row(row, line_no, file_stem)` | 한 줄 검사 → 이슈 dict 목록 |
| `.run_audit()` | 전체 검사 + CSV 2개 저장 + 결과 dict 반환 (`total_images`, `total_labels`, `empty_labels`, `total_bboxes`, `issues_count`, `class_counts`, `scene_counts`, `source_counts`, `split_counts`, `issue_csv`, `summary_csv`) |

### 이슈 코드

| 코드 | 조건 |
|---|---|
| `MISSING_IMAGE` / `MISSING_LABEL` | 짝 없음 |
| `COLUMN_COUNT` | 값이 5개가 아님 |
| `PARSE_ERROR` | 숫자로 바꿀 수 없음 |
| `CLASS_RANGE` | Class 가 0~6 밖 |
| `CLASS4_REVIEW` | Class 4 사용 |
| `CENTER_OUT_OF_RANGE` | 중심 x, y 가 0~1 밖 |
| `SIZE_OUT_OF_RANGE` | w, h 가 (0, 1] 밖 |

### 출력 파일

| 파일 | 내용 |
|---|---|
| `reports/audit_issue.csv` | `file, line, issue, detail` (UTF-8, BOM 없음) |
| `reports/audit_summary.csv` | `Category, Item, Count` — Overview · Class BBox · Scene Type · Source Dataset · Original Split (UTF-8 BOM) |

## 의존성

- **사용하는 것**: `pandas`, `csv`
- **사용하는 곳**: [`scripts/02_audit_subject7_final`](../scripts/02_audit_subject7_final.md), [`scripts/03_build_split`](../scripts/03_build_split.md) (`CLASS_NAMES`)

## 주의사항

- **파일을 이름(stem)만으로 짝짓는다.** `images/train/a.jpg` 와 `images/validation/a.jpg` 처럼 split 이 달라도 이름이 같으면 하나로 합쳐져 한쪽이 빠진다. (교과 7 최종본은 이름이 겹치지 않도록 만들어졌다 — [`build_final`](../../tools/build_final.md))
- 라벨을 `utf-8` 로 읽는다 (BOM 무시 안 함). Windows 메모장으로 저장해 BOM 이 붙은 파일은 첫 줄이 `PARSE_ERROR` 가 된다. 교과 7 쪽은 `utf-8-sig` 로 읽는다.
- `.png` 도 이미지로 센다 (교과 7 은 JPG 만).
- BBox 가 이미지 경계를 넘는지(`BOX_OUT_OF_IMAGE`), 중복 BBox 는 검사하지 않는다.
- Class 범위가 `0~6` 으로 코드에 고정되어 있다.
