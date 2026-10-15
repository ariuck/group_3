# Baseline 학습 조건 (`baseline_v1`)

> **이름 정리 (2026-10-14)**: kimchi_v1 의 첫 Baseline (이력). 이 모델의 실패 분석이 Dataset v2~v4 수정의 근거다. 공식 Baseline 은 `baseline_v4` (kimchi_v4 · YOLO11n · imgsz 640) — [`baseline_training_condition.md`](baseline_training_condition.md).


> 자동 생성: `train_detector.py` · 2026-10-14 09:59

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11n (`yolo11n.pt`, COCO 사전학습 · pretrained=True) |
| Dataset Version | `kimchi_v1` |
| Train / Val Manifest | `manifests/train.csv` 574장 (sha256 323671f45be8) / `manifests/val.csv` 84장 (sha256 b052c41d7942) |
| Data 설정 | `configs/dataset.yaml` (Class ID 0~6, Class 4 미사용) |
| Epoch | 50 |
| Batch | 16 |
| Image Size | 640 |
| Seed | 42 (deterministic=True) |
| Optimizer | AdamW |
| Learning Rate (lr0) | 0.001 |
| Augmentation | Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등) |

## 실행 환경

| 항목 | 값 |
|---|---|
| GPU | NVIDIA GeForce RTX 3060 (device 0) |
| GPU 최대 사용 메모리 | 2.1 GB |
| Ultralytics | 8.4.175 |
| PyTorch / CUDA | 2.14.1+cu130 / 13.0 |
| 학습 시작 | 2026-10-14 09:54:24 |
| 학습 종료 | 2026-10-14 09:59:13 |
| 걸린 시간 | 4분 49초 |
| 실행 폴더 | `runs/baseline_v1` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/baseline_v1/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/baseline_v1/weights/last.pt` |
| results.csv 생성 | ✅ | 50 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Baseline Weight 별도 보관 | ✅ | `models/baseline/baseline_v1_best.pt` (sha256 d69196de5620) |

## 메모

- Frozen Test(test.csv)와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 data/yolo/train·val 이 manifest 와 정확히 같은지 확인했다.
- 이 Weight 는 Smoke Test Weight 가 아니라 확정된 Train 전체로 학습한 첫 기준 모델이다.
- Validation 공식 평가와 `reports/baseline_v1_metrics.csv` 는 5일차에 작성한다.
- 참고 — best.pt 가 저장된 epoch 45 의 학습 중 Validation: P 0.428 · R 0.479 · mAP50 0.491 · mAP50-95 0.347
