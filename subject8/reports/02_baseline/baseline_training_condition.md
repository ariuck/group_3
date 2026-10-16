# Baseline 학습 조건 (`baseline_v4`)

> 자동 생성: `train_detector.py` · 2026-10-14 14:28

## 학습 조건

| 항목 | 값 |
|---|---|
| Model | YOLO11n (`yolo11n.pt`, COCO 사전학습 · pretrained=True) |
| Dataset Version | `kimchi_v4` |
| Train / Val Manifest | `manifests/train.csv` 526장 (sha256 169e6cfcb1f7) / `manifests/val.csv` 132장 (sha256 20c40a376464) |
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
| 학습 시작 | 2026-10-14 14:23:38 |
| 학습 종료 | 2026-10-14 14:28:14 |
| 걸린 시간 | 4분 36초 |
| 실행 폴더 | `runs/baseline_v4` |

## 학습 점검 (가이드 17.4)

| 항목 | 결과 | 내용 |
|---|:---:|---|
| best.pt 생성 | ✅ | `runs/baseline_v4/weights/best.pt` |
| last.pt 생성 | ✅ | `runs/baseline_v4/weights/last.pt` |
| results.csv 생성 | ✅ | 50 epoch 기록 |
| 매 Epoch Validation 실행 | ✅ | metrics/mAP50(B) 칸이 모든 epoch 에 있음 |
| Loss NaN/inf 없음 | ✅ | 이상 값 0칸 |
| Baseline Weight 별도 보관 | ✅ | `models/baseline/baseline_best.pt` (sha256 e732b7d16153) |

## 메모

- Frozen Test(test.csv)와 Bridge Holdout 은 학습·검증에 사용하지 않았다. 학습 전 data/yolo/train·val 이 manifest 와 정확히 같은지 확인했다.
- 이 Weight 는 kimchi_v4 확정 Train 전체로 학습한 공식 기준 모델이다. 개선 실험(exp001 = imgsz 1280)은 같은 Version·같은 Val 에서 비교한다.
- 이력: kimchi_v1 첫 Baseline(`baseline_v1`)의 실패 분석으로 Dataset 을 v2~v4 로 고쳤고, 가이드 11.5·20.5 에 따라 같은 Version 에서 Baseline 을 다시 학습했다.
- Validation 공식 평가와 `reports/02_baseline/baseline_metrics.csv` 는 `scripts/07_evaluate_baseline.py` 로 작성한다.
- 참고 — best.pt 가 저장된 epoch 50 의 학습 중 Validation: P 0.836 · R 0.674 · mAP50 0.764 · mAP50-95 0.534
