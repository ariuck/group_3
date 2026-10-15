# Smoke Test 기록 (진행용)

> 자동 생성: `train_detector.py` · 2026-10-14 09:53

## 학습 조건

| 항목 | 값 |
|---|---|
| 목적 | 학습 Pipeline 확인 (성능 판단 X) |
| Model | yolo11n.pt (사전학습) |
| Dataset | `configs/smoke_dataset.yaml` — data/yolo 의 train 40장 / val 8장 (seed 42) |
| Epoch | 3 |
| Image Size | 640 |
| Batch | 16 |
| Seed | 42 |
| Optimizer / lr0 | AdamW / 0.001 |

## 실행 환경

| 항목 | 값 |
|---|---|
| GPU | NVIDIA GeForce RTX 3060 (device 0) |
| GPU 최대 사용 메모리 | 2.1 GB |
| Ultralytics | 8.4.175 |
| PyTorch / CUDA | 2.14.1+cu130 / 13.0 |
| 학습 시작 | 2026-10-14 09:52:46 |
| 학습 종료 | 2026-10-14 09:53:01 |
| 걸린 시간 | 0분 15초 |
| 실행 폴더 | `runs/smoke_v1` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/smoke_v1/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/smoke_v1/weights/last.pt` |
| results.csv 생성 | ✅ | 3 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| 이미지 Prediction 실행 | ✅ | 250410_155009160971.jpg (conf 0.01) → BBox 112개, 저장 `runs/smoke_v1_predict` |
| BBox · Class · Confidence 표시 | ✅ | disease_browning 0.12, disease_browning 0.1, insect 0.07, disease_browning 0.07, plastic_stone_metal 0.07 |

## 메모

- Frozen Test 와 Bridge Holdout 은 사용하지 않았다.
- Smoke Weight 는 Baseline 으로 쓰지 않는다 (4일차에 전체 Train 으로 Baseline 학습).
