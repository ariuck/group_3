# `subject8/src/inference.py`

> 예측 박스를 정답(GT)과 짝지어 TP · CLASS_ERROR · FP · FN 으로 나누고, 정답과 예측을 나란히 그린 비교 이미지를 만든다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../../../subject8/src/inference.py)

## 역할

- 숫자(mAP)만이 아니라 **실제 사진에서 무엇을 맞히고 무엇을 틀리는지** 눈으로 보게 한다 (가이드 18장, 6일차 Failure Analysis 준비).

## 판정 규칙 (IoU 0.5)

| 판정 | 조건 | 뜻 |
|---|---|---|
| `TP` | 같은 Class, IoU ≥ 0.5 | 맞힘 |
| `CLASS_ERROR` | IoU ≥ 0.5 인데 Class 가 다름 | 위치는 맞고 종류를 틀림 |
| `FP` | 어떤 정답과도 IoU ≥ 0.5 가 아님 (같은 정답에 두 번째로 겹친 예측 포함) | 없는 이물을 있다고 함 |
| `FN` | 어떤 예측과도 짝지어지지 않은 정답 | 이물을 놓침 |

확신도가 높은 예측부터 짝짓고, 1차로 같은 Class(TP), 2차로 남은 것 중 위치만 맞는 것(CLASS_ERROR)을 찾는다.

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `IOU_THRESHOLD` | `0.5` |
| `COLORS` | Class 별 박스 색 (BGR) |
| `load_gt(label_path)` | YOLO TXT → `[(cls, x1, y1, x2, y2)]` (0~1 비율, BOM 무시) |
| `iou(a, b)` | 두 박스의 IoU |
| `match(gt, preds)` | `preds = [(cls, conf, x1, y1, x2, y2)]` → `pred_kind`({예측 번호: (판정, 짝 정답 번호)}), `fn`(놓친 정답 번호), `tp`, `class_error`, `fp`, `fn_count` |
| `draw_comparison(image_path, gt, preds, result, names, out_path, max_width=1600)` | 왼쪽 정답 · 오른쪽 예측 이미지 저장. 예측: TP 실선, CLASS_ERROR 노랑 테두리, FP 빨강 테두리. 놓친 정답: 왼쪽에 빨강 X. 위쪽 띠에 개수 요약 |

## 의존성

- **사용하는 것**: `opencv-python` (ultralytics 설치 시 함께 설치됨)
- **사용하는 곳**: [`scripts/08_predict_images`](../scripts/08_predict_images.md)

## 주의사항

- 이 집계는 **한 conf 기준(예: 0.25)에서의 개수**다. mAP 처럼 모든 기준을 평균한 값이 아니므로 숫자가 다르다.
- 4K 원본을 가로 1600px 로 줄여 그린다 (보기용). 판정은 비율 좌표로 하므로 크기와 무관하다.
- 비교 이미지에는 회사 사진이 들어가므로 `runs/` 아래에만 저장한다 (Git 제외).
