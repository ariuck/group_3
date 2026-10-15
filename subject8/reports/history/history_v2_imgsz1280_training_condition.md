# 데이터 개선 이력 학습 조건 (`history_v2_imgsz1280`, 처음 이름 `baseline_kimchi_v2`)

> **이름 정리 (2026-10-14)**: kimchi_v2 데이터 개선 이력 (imgsz 1280). 공식 Baseline 은 `baseline_v4` (kimchi_v4 · YOLO11n · imgsz 640) — [`baseline_training_condition.md`](../02_baseline/baseline_training_condition.md).


> 자동 생성: `train_detector.py` · 2026-10-14 11:27

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11n (`yolo11n.pt`, COCO 사전학습 · pretrained=True) |
| Dataset Version | `kimchi_v2` |
| Train / Val Manifest | `manifests/train.csv` 551장 (sha256 6a17ae7b6237) / `manifests/val.csv` 107장 (sha256 86812755c352) |
| Data 설정 | `configs/dataset.yaml` (Class ID 0~6, Class 4 미사용) |
| Epoch | 50 |
| Batch | 16 |
| Image Size | 1280 |
| Seed | 42 (deterministic=True) |
| Optimizer | AdamW |
| Learning Rate (lr0) | 0.001 |
| Augmentation | Ultralytics 기본값 (mosaic, 좌우반전 0.5, HSV 등) |

## 실행 환경

| 항목 | 값 |
|---|---|
| GPU | NVIDIA GeForce RTX 3060 (device 0) |
| GPU 최대 사용 메모리 | 8.4 GB |
| Ultralytics | 8.4.175 |
| PyTorch / CUDA | 2.14.1+cu130 / 13.0 |
| 학습 시작 | 2026-10-14 11:17:08 |
| 학습 종료 | 2026-10-14 11:27:33 |
| 걸린 시간 | 10분 24초 |
| 실행 폴더 | `runs/history_v2_imgsz1280` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/history_v2_imgsz1280/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/history_v2_imgsz1280/weights/last.pt` |
| results.csv 생성 | ✅ | 50 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Weight 별도 보관 | ✅ | `models/improved/history_v2_imgsz1280_best.pt` (sha256 7bf9b0e100a9) |

## 메모

- Frozen Test(test.csv)와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 data/yolo/train·val 이 manifest 와 정확히 같은지 확인했다.
- kimchi_v2 Split(G00 파/고추 구간 분할, G12 가운데 배치 Train, G05 Val)로 학습한 새 기준 모델이다. baseline_v1(kimchi_v1)과는 Val 구성이 달라 Validation 점수를 직접 비교하지 않는다.
- imgsz 1280 은 kimchi_v1 예비 실험 pilot_v1_imgsz1280(mAP50-95 0.351 → 0.519) 결과로 정했다.
- 참고 — best.pt 가 저장된 epoch 47 의 학습 중 Validation: P 0.697 · R 0.672 · mAP50 0.708 · mAP50-95 0.575
