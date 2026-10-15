# `subject8_kimchi_detection/src/dataset_audit.py`

> 교과 7 최종본의 YOLO 라벨을 점검하는 `DatasetAuditor`. 짝·열 개수·Class 범위·Class 4·좌표 범위·사진 밖 BBox·이름 중복·검수표 대조를 검사하고, 요약·이슈·Class×장면 CSV 를 만든다.

[← 코드 문서 목차](../../README.md) · [코드 보기](../../../../subject8_kimchi_detection/src/dataset_audit.py)

## 역할

- 교과 8 에서 학습 전에 넘겨받은 데이터가 학습 가능한 상태인지 확인한다 (가이드 15.1).
- Class 분포와 장면(scene_type) 분포를 함께 집계한다 (가이드 15.2).
- 교과 7 의 [`validator`](../../src/validation/validator.md) 와 비슷한 검사를 교과 8 쪽에서 독립적으로 다시 한다 (영문 Class 이름 사용).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `CLASS_NAMES` | `{0: leaf_paper, 1: plastic_stone_metal, 2: branch, 3: insect, 4: rubber_glove_unused, 5: disease_browning, 6: green_onion_pepper}` |
| `SCENE_TYPES` | 검수표 `이미지 유형` → 영문 scene_type (`김치+대상 객체` → `kimchi_with_target`, `정상 김치` → `normal_kimchi`, `대상 객체 단독` → `object_only`, `판단 어려움` → `other_review`) |
| `BOX_EDGE_TOLERANCE` | 사진 밖 BBox 로 볼 최소 초과량 `1e-6` (소수점 오차 허용) |
| `DatasetAuditor(data_root, report_dir)` | `data_root/images`, `data_root/labels`, `data_root/검수표.csv` 를 읽음. 보고서 폴더 생성 |
| `.validate_yolo_row(row, line_no, file_stem)` | 한 줄 검사 → 이슈 dict 목록 |
| `.run_audit()` | 전체 검사 + CSV 3개 저장 + 결과 dict 반환 |

`run_audit()` 반환 키: `total_images`, `total_labels`, `empty_labels`, `total_bboxes`, `issues_count`, `class_counts`, `scene_counts`, `source_counts`, `split_counts`, `bbox_per_image`(min·median·mean·max), `bbox_distribution`({박스 수: 사진 수}), `class_scene`({Class: {이미지 유형: 사진 수}}), `issue_csv`, `summary_csv`, `class_scene_csv`

### 이슈 코드

| 코드 | 조건 |
|---|---|
| `MISSING_IMAGE` / `MISSING_LABEL` | 짝 없음 |
| `DUPLICATE_STEM` | 하위 폴더(train/validation)에 같은 이름의 사진 또는 TXT 가 있음. 첫 파일만 쓰고 기록 |
| `COLUMN_COUNT` | 값이 5개가 아님 |
| `PARSE_ERROR` | 숫자로 바꿀 수 없음 |
| `CLASS_RANGE` | Class 가 0~6 밖 |
| `CLASS4_REVIEW` | Class 4 사용 |
| `CENTER_OUT_OF_RANGE` | 중심 x, y 가 0~1 밖 |
| `SIZE_OUT_OF_RANGE` | w, h 가 (0, 1] 밖 |
| `BOX_OUT_OF_IMAGE` | 중심·크기는 정상인데 박스 가장자리가 사진 밖 (`x ± w/2`, `y ± h/2` 가 0~1 밖) |
| `NOT_IN_MANIFEST` | 사진이 `검수표.csv` 에 없음 |
| `EMPTY_NOT_NORMAL` | 빈 TXT 인데 검수표 `이미지 유형` 이 `정상 김치` 가 아님 (가이드 15.1 "Empty TXT 는 FINAL 기록과 대조") |

### 출력 파일

| 파일 | 내용 |
|---|---|
| `reports/audit_issue.csv` | `file, line, issue, detail` (UTF-8, BOM 없음) |
| `reports/audit_summary.csv` | `Category, Item, Count` — Overview · Class BBox · BBox per Image · BBox per Image Distribution · Scene Type · Source Dataset · Original Split (UTF-8 BOM) |
| `reports/audit_class_scene.csv` | `class_id, class_name, images_total, kimchi_with_target, object_only, …` — 각 Class 가 들어 있는 **사진 수**를 장면 유형별로 (UTF-8 BOM) |

## 의존성

- **사용하는 것**: `pandas`, `csv`, `statistics`
- **사용하는 곳**: [`scripts/02_audit_subject7_final`](../scripts/02_audit_subject7_final.md), [`scripts/03_build_split`](../scripts/03_build_split.md) (`CLASS_NAMES`)

## 주의사항

- 라벨은 `utf-8-sig` 로 읽는다. Windows 메모장으로 저장해 BOM 이 붙은 TXT 도 정상으로 읽힌다.
- `.png` 도 이미지로 센다 (교과 7 은 JPG 만).
- 같은 BBox 가 두 번 들어간 중복 BBox 는 검사하지 않는다.
- Class 범위가 `0~6` 으로 코드에 고정되어 있다.
- 검수표가 없거나 `이미지 파일명`·`이미지 유형` 칸이 없으면 `NOT_IN_MANIFEST`·`EMPTY_NOT_NORMAL` 대조와 Class×장면 표를 건너뛴다 (장면은 `unknown`).
