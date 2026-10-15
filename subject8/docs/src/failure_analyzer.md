# `subject8/src/failure_analyzer.py`

> 모델이 틀린 것을 모아 실패 유형(FN · CLASS_ERROR · FP 3종)으로 나누고, 크기별 Recall · Train/Val 박스 크기 차이 · 대표 실패 사진 모음을 만든다 (6일차 Failure Analysis).

[← 코드 문서 목차](../README.md) · [코드 보기](../../src/failure_analyzer.py)

## 역할

- 가이드 예시 6 `failure_analyzer.py`. "성능이 낮다"가 아니라 "무엇을 왜 틀리는가"를 구체적으로 말할 근거를 만든다.
- FP 를 세 가지로 더 나눠 **추론 설정 문제(같은 물체 두 Class)**, **박스 기준 차이**, **배경 혼동/라벨 누락 후보**를 구분한다.

## 실패 유형

| 유형 | 조건 |
|---|---|
| `FN` | 짝지어지지 않은 정답 |
| `CLASS_ERROR` | IoU ≥ 0.5 인데 Class 가 다름 |
| `FP_DUPLICATE` | 예측이 이미 짝지어진 정답과 IoU ≥ 0.5 (같은 물체를 두 번째 Class 로 예측) |
| `FP_PARTIAL` | 정답과 조금 겹침 (0 < IoU < 0.5, 또는 중심이 정답 박스 안) |
| `FP_BACKGROUND` | 근처에 정답이 없음 |

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `SIZE_BUCKETS` | 4K 원본 박스 한 변(√넓이) 기준 S < 150px · M < 300px · L |
| `collect_failures(model_path, images_dir, labels_dir, meta, conf=0.25, imgsz=640)` | 예측 1회 → (실패 목록, 정답별 결과 목록). 실패 행: `image, capture_group, scene_type, failure_type, gt_class, pred_class, conf, size_px, size_bucket, best_iou, cause_hint, x1, y1, x2, y2` |
| `cause_hint(kind, px)` | 규칙 기반 1차 힌트 (`same_object_two_classes`, `background_confusion_or_missing_label`, `box_position_or_size`, `small_object`, `appearance_or_class_confusion`). 최종 판단은 사람 |
| `recall_by_size(gt_rows, names)` | Class × 크기 구간 Recall |
| `box_size_shift(labels_train, labels_val, names)` | Class 별 정답 박스 크기 중앙값 Train vs Val (`val_to_train` 비율) — 같은 Class 인데 모습이 다른지 보는 단서 |
| `class_montage(cls, name, splits, meta, out_path)` | 같은 Class 정답 박스를 Train / Val 16개씩 잘라 위아래 비교 |
| `failure_montage(failures, failure_type, images_dir, out_path)` | 실패 유형별 대표 24개 (확신도 높은 순) |
| `summarize(failures)` | 실패 유형 × Class 개수 |

## 의존성

- **사용하는 것**: [`src/inference`](inference.md) (`load_gt`, `iou`, `match`), `ultralytics.YOLO`, `opencv-python`
- **사용하는 곳**: [`scripts/09_collect_failures`](../scripts/09_collect_failures.md)

## 주의사항

- 박스 크기는 4K(4848×2704) 기준이다 (`box_size_shift` 의 기본값). 해상도가 다른 데이터면 인자를 바꾼다.
- 집계는 한 conf 기준이다. mAP 와 숫자가 다르다.
- 사진 모음은 회사 사진이므로 `demo/` 아래 jpg 로만 저장한다 (`.gitignore` 로 제외).
