# `subject8/src/tiling.py`

> 타일링 — 4K 원본을 겹치는 조각으로 잘라 학습용 사진·라벨을 만들고, 조각별 예측을 원본 좌표로 합쳐 **원본 사진 단위로 채점**한다.

[← 코드 문서 목차](../README.md) · [코드 보기](../../src/tiling.py)

## 역할

- 1920 으로 줄이면 작은 이물(작은 갈변 한 변 20~30px)이 10px 안팎으로 사라지는 문제를, 2×2 조각(축소 약 1.4배)으로 줄이는 실험([`14_train_tiles_v5`](../scripts/14_train_tiles_v5.md))에 쓴다.
- 조각 모델과 원본 모델을 **같은 채점 코드**로 비교한다 (조각 단위 점수는 다른 실험과 비교할 수 없음).

## 주요 구성요소

| 이름 | 설명 |
|---|---|
| `tile_windows(w, h, grid=(2,2), overlap=0.2)` | 조각 창 `[(x0, y0, x1, y1)]`. 4848×2704 → 2693×1502 조각 4개 |
| `tile_labels(boxes, win, w, h, min_visible=0.4)` | 원본 박스 → 조각 YOLO 줄. 조각 안에 보이는 넓이가 40% 미만이면 뺀다 |
| `write_tiles(image, label, out_images, out_labels, grid, overlap)` | 사진 1장 → 조각 JPG(품질 95)·TXT (`<이름>_t<번호>`) |
| `predict_full(model, img, imgsz, tiles=None, …)` | 원본 예측 `[[x1, y1, x2, y2, conf, cls]]`. `tiles` 를 주면 조각별 예측을 옮겨 붙이고 Class 별 NMS(IoU 0.6)로 겹친 것을 합친다 |
| `match_predictions(pred_cls, true_cls, iou)` | Ultralytics `DetectionValidator` 와 같은 짝짓기 (IoU 0.50~0.95, 10단계) |
| `evaluate_full(model, pairs, imgsz, tiles=None)` | `[(사진, 라벨)]` → 전체·Class 별 P·R·mAP50·mAP50-95 (`ultralytics.utils.metrics.ap_per_class`) |

## 의존성

- **사용하는 것**: [`src/inference`](inference.md) (`load_gt`), [`src/constants`](constants.md) (`CLASS_NAMES`), `ultralytics`, `torch`·`torchvision`, `opencv`
- **사용하는 곳**: [`scripts/14_train_tiles_v5`](../scripts/14_train_tiles_v5.md)

## 주의사항

- 예측은 사진 1장씩(`conf 0.001`, `iou 0.7`, `max_det 300`). Ultralytics `val` (사각 배치)과 약간 달라, exp002_v5 Val mAP50-95 가 `val` 0.704 · 이 코드 0.680 으로 나온다. **모델끼리는 이 코드로만 비교한다.**
- 원본 학습 모델에 조각 예측만 쓰면 오히려 떨어진다 (exp002_v5: 0.680 → 0.575). 조각으로 학습해야 한다.
