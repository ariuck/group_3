# `subject8/src/evaluate_detector.py`

> 학습된 Weight 의 검출 성능(Precision · Recall · mAP50 · mAP50-95, Class 별)을 측정한다. Baseline · 개선 실험 · Final 평가가 모두 이 함수를 쓴다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../../subject8/src/evaluate_detector.py)

## 역할

- 가이드 18.1 `evaluate_detector` 구현. "학습이 끝났다"가 아니라 "얼마나 잘 검출하는가"를 숫자로 확인한다.
- **Frozen Test 보호**: `split="test"` 는 `allow_test=True` 일 때만 실행한다 (8일차 Final 확정 후).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `evaluate_detector(model_path, data_yaml, split, imgsz, batch=16, project="runs", name="eval", allow_test=False)` | `model.val()` 실행 → 전체 지표 + Class 별 지표 dict. PR 곡선·Confusion Matrix 를 `project/name` 에 저장 |
| `count_split_images(data_yaml, split)` | `dataset.yaml` 의 `path/<split>` 폴더 사진 수 |

반환 키: `split, images, instances, precision, recall, map50, map50_95, per_class, save_dir, speed_ms`

`per_class` 행: `class_id, class_name, images, instances, precision, recall, map50, map50_95, note` — 정답이 0건인 Class(4번)는 값 대신 `note="Instance 0건 — 평가 불가"`.

## 의존성

- **사용하는 것**: `ultralytics.YOLO`, `PyYAML`
- **사용하는 곳**: [`scripts/07_evaluate_baseline`](../scripts/07_evaluate_baseline.md)

## 주의사항

- `imgsz` 는 학습 때와 같은 값으로 평가해야 비교가 공정하다 (07 은 `runs/<실행>/args.yaml` 에서 읽음).
- Ultralytics `val()` 의 conf 기본값은 0.001 이다. mAP 는 모든 confidence 구간을 보므로 낮은 값이 맞다. 사진에 그려 보는 [`08_predict_images`](../scripts/08_predict_images.md) 의 conf(기본 0.25)와 다르다.
- `data_yaml` 의 상대 `path:` 는 현재 폴더 기준 → 호출 스크립트가 프로젝트 루트로 `os.chdir` 한다.
